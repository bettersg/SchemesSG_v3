"""
Firestore Trigger for New Scheme Entries.

Triggers when a new document is created in schemeEntries collection.
Calls the scheme-processor Cloud Run service for processing.
"""

import json
import os
import time
from datetime import datetime, timezone

import google.auth
import google.auth.compute_engine
import google.auth.transport.requests
import requests
from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import firestore_fn, options
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.oauth2 import service_account
from loguru import logger
from slack_sdk.web import WebClient
from utils.json_utils import safe_json_dumps
from utils.scheme_lifecycle import retirement_validation_error

from new_scheme.new_scheme_blocks import build_new_scheme_duplicate_message, build_scheme_retirement_review_message
from new_scheme.url_utils import check_duplicate_scheme


# URL for scheme-processor service
# In local dev: http://scheme-processor:8081 (docker network)
# In production: Cloud Run URL
PROCESSOR_SERVICE_URL = os.getenv("PROCESSOR_SERVICE_URL", "http://localhost:8081")

# Firestore-triggered functions cap out at 540s.
FUNCTION_TIMEOUT_SEC = 540
# Above the processor's 300s Cloud Run timeout, so its own timeout response arrives first.
PROCESSOR_TIMEOUT_SEC = 330
PROCESSOR_MAX_ATTEMPTS = 3
PROCESSOR_RETRY_DELAYS_SEC = (15, 45)
# 503: instance killed (out of memory) or not ready. 429: every instance busy. The processor
# posts the review card last, so these are retried unless that card already exists. Timeouts
# and 504s are not retried: the processor may still be running and would process twice.
PROCESSOR_RETRY_STATUSES = {429, 503}


class ProcessorStillRunning(Exception):
    """The connection dropped after the processor started this attempt, so it may still finish."""


def get_identity_token(audience: str) -> str:
    """Get identity token for Cloud Run authentication."""
    # Try to get credentials from GOOGLE_APPLICATION_CREDENTIALS (service account)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            creds_path, target_audience=audience
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        return credentials.token

    # Fallback to compute engine credentials (works on GCP - Cloud Functions/Run)
    auth_req = google.auth.transport.requests.Request()
    credentials = google.auth.compute_engine.IDTokenCredentials(
        request=auth_req,
        target_audience=audience,
        use_metadata_identity_endpoint=True,
    )
    credentials.refresh(auth_req)
    return credentials.token


def get_slack_client() -> WebClient:
    """Get Slack WebClient instance."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")
    return WebClient(token=bot_token)


def get_slack_channel() -> str:
    """Get Slack channel ID for notifications."""
    channel = os.getenv("SLACK_CHANNEL_ID")
    if not channel:
        raise ValueError("SLACK_CHANNEL_ID environment variable not set")
    return channel


def process_scheme_retirement_entry(doc_id: str, data: dict) -> None:
    """Validate a retirement request and send it directly to Slack review."""
    db = get_firestore_client()
    entry_ref = db.collection("schemeEntries").document(doc_id)
    target_scheme_id = data.get("targetSchemeId")
    reason = data.get("retiredReason")
    merged_into = data.get("mergedInto")

    try:
        if not target_scheme_id or not isinstance(target_scheme_id, str):
            raise ValueError("Retirement request requires targetSchemeId")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Retirement request requires retiredReason")
        target_snap = db.collection("schemes").document(target_scheme_id).get()
        if not target_snap.exists:
            raise ValueError(f"Target scheme {target_scheme_id!r} does not exist")
        target_data = target_snap.to_dict() or {}

        validation_error = retirement_validation_error(target_scheme_id, merged_into)
        if validation_error:
            raise ValueError(validation_error)

        merge_target_data = None
        merge_target_exists = True
        if merged_into:
            merge_snap = db.collection("schemes").document(merged_into).get()
            merge_target_data = merge_snap.to_dict() if merge_snap.exists else {}
            merge_target_exists = merge_snap.exists

        validation_error = retirement_validation_error(
            target_scheme_id,
            merged_into,
            merge_target_exists=merge_target_exists,
            merge_target_data=merge_target_data,
        )
        if validation_error:
            raise ValueError(validation_error)

        entry_ref.update(
            {
                "pipeline_status": "awaiting_approval",
                "pipeline_completed_at": datetime.now(timezone.utc).isoformat(),
                "Scheme": target_data.get("scheme", data.get("Scheme")),
                "Link": target_data.get("link", data.get("Link")),
            }
        )

        slack_client = get_slack_client()
        channel = get_slack_channel()
        message = build_scheme_retirement_review_message(doc_id, data, target_data, merge_target_data)
        response = slack_client.chat_postMessage(channel=channel, **message)
        if response.get("ok"):
            entry_ref.update(
                {
                    "slack_channel": channel,
                    "slack_message_ts": response.get("ts"),
                    "slack_notified_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        logger.info(f"Posted retirement request to Slack for {doc_id}")
    except Exception as e:
        logger.error(f"Failed to process retirement request {doc_id}: {e}")
        _update_error_status(doc_id, str(e))


def process_new_scheme_entry(doc_id: str, data: dict) -> None:
    """
    Process a new scheme entry by calling Cloud Run service.

    In local dev: calls local Docker container (scheme-processor:8081)
    In production: calls Cloud Run endpoint

    The scheme-processor service handles:
    1. Web scraping with crawl4ai + Playwright
    2. LLM field extraction
    3. Contact extraction (regex)
    4. Planning area lookup
    5. Firestore update
    6. Slack posting

    Args:
        doc_id: Document ID from schemeEntries
        data: Document data
    """
    started = time.monotonic()
    logger.info(f"Processing scheme entry: {doc_id}")
    logger.info(f"Data: {json.dumps(data, default=str)[:500]}")

    # Check if this is a warmup or test entry
    if data.get("is_warmup") or data.get("is_test"):
        logger.info(f"Skipping warmup/test entry: {doc_id}")
        return

    # Retirement is terminal and does not need scraping or LLM processing.
    type_of_request = (data.get("typeOfRequest") or "").lower()
    if type_of_request == "retire":
        process_scheme_retirement_entry(doc_id, data)
        return

    # Only process new scheme submissions and update-in-place requests.
    if type_of_request not in ("new", "update"):
        logger.info(f"Skipping non-new/update entry (type={type_of_request}): {doc_id}")
        return

    target_scheme_id = data.get("targetSchemeId") if type_of_request == "update" else None

    # Check if already processed (prevent duplicate processing)
    if data.get("pipeline_status") == "processed":
        logger.info(f"Entry already processed: {doc_id}")
        return

    # Check for duplicate URL (keep this in Firebase Functions for speed)
    link = data.get("Link", "")
    duplicate = check_duplicate_scheme(link, exclude_doc_id=target_scheme_id)
    # An update keeps going: the page has likely changed, so a maintainer still reviews the
    # scraped fields, with a warning on the card that another scheme has this link.
    if duplicate and type_of_request != "update":
        logger.warning(f"Duplicate URL detected for {doc_id}: {duplicate}")

        # Update schemeEntries with duplicate status
        db = get_firestore_client()
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update(
            {
                "pipeline_status": "duplicate",
                "pipeline_error": f"This URL already exists: {duplicate['scheme']} ({duplicate['link']})",
                "duplicate_scheme_id": duplicate["doc_id"],
                "duplicate_scheme_name": duplicate["scheme"],
                "duplicate_normalized_url": duplicate["normalized_url"],
            }
        )

        # Post to Slack with duplicate warning
        post_duplicate_to_slack(doc_id, data, duplicate)
        return

    # Call scheme-processor Cloud Run service
    logger.info(f"Calling scheme-processor for {doc_id} at {PROCESSOR_SERVICE_URL}")
    try:
        # Serialize data to JSON string first to handle datetime objects, then parse back
        serialized_data = json.loads(safe_json_dumps(data))

        # Get identity token for Cloud Run auth (skip for local dev http URLs)
        headers = {"Content-Type": "application/json"}
        if PROCESSOR_SERVICE_URL.startswith("https://"):
            try:
                token = get_identity_token(PROCESSOR_SERVICE_URL)
                headers["Authorization"] = f"Bearer {token}"
                logger.info(f"Got identity token for Cloud Run auth (token length: {len(token)})")
            except Exception as auth_error:
                logger.error(f"Failed to get identity token: {auth_error}")

        response = _post_to_processor(
            doc_id,
            {
                "doc_id": doc_id,
                "scheme_name": data.get("Scheme", "Unknown"),
                "scheme_url": data.get("Link", ""),
                "original_data": serialized_data,
                "type_of_request": type_of_request,
                "target_scheme_id": target_scheme_id,
            },
            headers,
            started,
        )
        if response is None:
            if duplicate:
                _warn_shared_link(doc_id, duplicate)
            return

        result = response.json()
        logger.info(f"Scheme-processor result for {doc_id}: {result}")

        if not result.get("success"):
            logger.error(f"Scheme-processor failed for {doc_id}: {result.get('error')}")
            _alert_pipeline_failure(doc_id, data, result.get("error") or "Unknown processor error")
        elif duplicate:
            _warn_shared_link(doc_id, duplicate)

    except ProcessorStillRunning as e:
        logger.warning(f"Scheme-processor connection for {doc_id} dropped after it started: {e}")
        _alert_outcome_unknown(doc_id, data, str(e), duplicate)

    except requests.exceptions.Timeout:
        logger.error(f"Scheme-processor timeout for {doc_id}")
        _fail_entry(doc_id, data, "Processing timeout - service did not respond in time")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Scheme-processor connection error for {doc_id}: {e}")
        _fail_entry(doc_id, data, f"Could not connect to processor service: {e}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Scheme-processor error for {doc_id}: {e}")
        _fail_entry(doc_id, data, str(e))


def _post_to_processor(doc_id: str, payload: dict, headers: dict, started: float) -> requests.Response | None:
    """
    POST to scheme-processor, retrying 429, 503 and connection errors while the function has time.

    `started` is the function's own start (time.monotonic()), so earlier work counts against the budget.

    Returns None when a retryable error arrives after the review card was posted: the
    processor finished, so the entry must not be retried or marked failed.

    Raises ProcessorStillRunning when a connection error arrives after the processor started
    this attempt: `requests` also raises ConnectionError for a reset after the POST was sent,
    and the processor keeps running, so a retry would process the entry twice.
    """
    for attempt in range(1, PROCESSOR_MAX_ATTEMPTS + 1):
        attempt_started = datetime.now(timezone.utc)
        try:
            response = requests.post(
                f"{PROCESSOR_SERVICE_URL}/process", json=payload, headers=headers, timeout=PROCESSOR_TIMEOUT_SEC
            )
            response.raise_for_status()
            return response
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            status = getattr(e.response, "status_code", None)
            connection_error = isinstance(e, requests.exceptions.ConnectionError)
            if not (connection_error or status in PROCESSOR_RETRY_STATUSES):
                raise
            entry = _read_entry(doc_id)
            if entry.get("slack_message_ts"):
                logger.warning(f"Scheme-processor error for {doc_id} after its review card was posted: {e}")
                return None
            if connection_error and _started_since(entry, attempt_started):
                raise ProcessorStillRunning(str(e)) from e
            if attempt == PROCESSOR_MAX_ATTEMPTS:
                raise
            delay = PROCESSOR_RETRY_DELAYS_SEC[attempt - 1]
            if time.monotonic() - started + delay + PROCESSOR_TIMEOUT_SEC > FUNCTION_TIMEOUT_SEC:
                logger.error(f"No time left to retry scheme-processor for {doc_id}")
                raise
            logger.warning(f"Scheme-processor attempt {attempt} for {doc_id} failed ({e}); retrying in {delay}s")
            time.sleep(delay)


def _read_entry(doc_id: str) -> dict:
    try:
        return get_firestore_client().collection("schemeEntries").document(doc_id).get().to_dict() or {}
    except Exception as e:
        logger.error(f"Failed to read {doc_id} before retrying: {e}")
        return {}


def _started_since(entry: dict, attempt_started: datetime) -> bool:
    """Whether the processor wrote `pipeline_started_at` at or after this attempt began."""
    try:
        return datetime.fromisoformat(entry["pipeline_started_at"]) >= attempt_started
    except (KeyError, TypeError, ValueError):
        return False


def _fail_entry(doc_id: str, data: dict, error_msg: str) -> None:
    _update_error_status(doc_id, error_msg)
    _alert_pipeline_failure(doc_id, data, error_msg)


def _alert_pipeline_failure(doc_id: str, data: dict, error_msg: str) -> None:
    """Tell maintainers a submission failed, so it is re-driven instead of silently dropped."""
    try:
        get_slack_client().chat_postMessage(
            channel=get_slack_channel(),
            text=(
                f":rotating_light: *Scheme submission failed processing.* `{doc_id}`\n"
                f"*{data.get('Scheme', 'Unknown')}*: {data.get('Link', '')}\n"
                f"Error: {error_msg}\n"
                "The entry is marked `failed` and has no review card. Re-drive it once the processor is healthy."
            ),
            unfurl_links=False,
        )
    except Exception as e:
        logger.error(f"Failed to post pipeline failure alert for {doc_id}: {e}")


def _alert_outcome_unknown(doc_id: str, data: dict, error_msg: str, duplicate: dict | None) -> None:
    """Tell maintainers the processor may still finish, so they check before re-driving."""
    shared_link = (
        f"\n:warning: This link also belongs to *{duplicate['scheme']}* (`{duplicate['doc_id']}`)."
        if duplicate
        else ""
    )
    try:
        get_slack_client().chat_postMessage(
            channel=get_slack_channel(),
            text=(
                f":hourglass: *Lost the connection to the scheme processor after it started.* `{doc_id}`\n"
                f"*{data.get('Scheme', 'Unknown')}*: {data.get('Link', '')}\n"
                f"Error: {error_msg}\n"
                "It was not retried, to avoid processing twice. It may still post a review card. "
                f"If none appears and the entry stays `processing`, re-drive it.{shared_link}"
            ),
            unfurl_links=False,
        )
    except Exception as e:
        logger.error(f"Failed to post outcome-unknown alert for {doc_id}: {e}")


def _warn_shared_link(doc_id: str, duplicate: dict) -> None:
    """Reply on an update's review card that its new link already belongs to another scheme."""
    try:
        entry = get_firestore_client().collection("schemeEntries").document(doc_id).get().to_dict() or {}
        if not (entry.get("slack_channel") and entry.get("slack_message_ts")):
            return
        get_slack_client().chat_postMessage(
            channel=entry["slack_channel"],
            thread_ts=entry["slack_message_ts"],
            reply_broadcast=True,
            text=(
                f":warning: *Same link as another scheme.* This new link already belongs to "
                f"*{duplicate['scheme']}* (`{duplicate['doc_id']}`): {duplicate['link']}\n"
                "Approving gives both schemes this link. If they are the same programme, reject this "
                f"and retire `{entry.get('targetSchemeId')}` with Merged into `{duplicate['doc_id']}` instead."
            ),
            unfurl_links=False,
        )
    except Exception as e:
        logger.error(f"Failed to post shared-link warning for {doc_id}: {e}")


def _update_error_status(doc_id: str, error_msg: str) -> None:
    """Update schemeEntries with error status."""
    try:
        db = get_firestore_client()
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update(
            {
                "pipeline_status": "failed",
                "pipeline_error": error_msg,
                "pipeline_failed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Failed to update error status for {doc_id}: {e}")


def post_duplicate_to_slack(doc_id: str, data: dict, duplicate_info: dict) -> None:
    """
    Post duplicate domain warning to Slack.

    Args:
        doc_id: Document ID from schemeEntries
        data: Original submission data
        duplicate_info: Info about existing duplicate scheme
    """
    try:
        slack_client = get_slack_client()
        channel = get_slack_channel()

        message = build_new_scheme_duplicate_message(doc_id, data, duplicate_info)
        slack_client.chat_postMessage(channel=channel, **message)

        logger.info(f"Posted duplicate warning to Slack for {doc_id}")
    except Exception as e:
        logger.error(f"Failed to post duplicate warning to Slack: {e}")


@firestore_fn.on_document_created(
    document="schemeEntries/{docId}",
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Lightweight - just calls Cloud Run service
    timeout_sec=FUNCTION_TIMEOUT_SEC,  # Includes waiting for Cloud Run response and retries
)
def on_new_scheme_entry(event: firestore_fn.Event[DocumentSnapshot]) -> None:
    """
    Firestore trigger: Triggered when a new document is created in schemeEntries collection.

    Calls scheme-processor Cloud Run service for heavy processing.
    In local dev (without Firestore emulator), update_scheme.py calls
    process_new_scheme_entry() directly.
    """
    doc_id = event.params["docId"]
    data = event.data.to_dict() if event.data else {}
    process_new_scheme_entry(doc_id, data)
