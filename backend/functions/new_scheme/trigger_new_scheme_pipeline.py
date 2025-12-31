"""
Firestore Trigger for New Scheme Entries.

Triggers when a new document is created in schemeEntries collection.
Calls the scheme-processor Cloud Run service for processing.
"""
import os
import json
from datetime import datetime, timezone

import requests
import google.auth
import google.auth.transport.requests
from google.oauth2 import service_account
from firebase_functions import firestore_fn, options
from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from slack_sdk.web import WebClient
from loguru import logger

from new_scheme.new_scheme_blocks import build_new_scheme_duplicate_message
from new_scheme.url_utils import check_duplicate_scheme
from utils.json_utils import safe_json_dumps

# URL for scheme-processor service
# In local dev: http://scheme-processor:8081 (docker network)
# In production: Cloud Run URL
PROCESSOR_SERVICE_URL = os.getenv("PROCESSOR_SERVICE_URL", "http://localhost:8081")


def get_identity_token(audience: str) -> str:
    """Get identity token for Cloud Run authentication."""
    # Try to get credentials from GOOGLE_APPLICATION_CREDENTIALS (service account)
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.exists(creds_path):
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            creds_path,
            target_audience=audience
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        return credentials.token

    # Fallback to Application Default Credentials (works on GCP)
    credentials, _ = google.auth.default()
    credentials = credentials.with_target_audience(audience)
    auth_req = google.auth.transport.requests.Request()
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
    logger.info(f"Processing scheme entry: {doc_id}")
    logger.info(f"Data: {json.dumps(data, default=str)[:500]}")

    # Check if this is a warmup or test entry
    if data.get("is_warmup") or data.get("is_test"):
        logger.info(f"Skipping warmup/test entry: {doc_id}")
        return

    # Only process new scheme submissions (not edit requests)
    type_of_request = data.get("typeOfRequest", "").lower()
    if type_of_request != "new":
        logger.info(f"Skipping non-new entry (type={type_of_request}): {doc_id}")
        return

    # Check if already processed (prevent duplicate processing)
    if data.get("pipeline_status") == "processed":
        logger.info(f"Entry already processed: {doc_id}")
        return

    # Check for duplicate URL (keep this in Firebase Functions for speed)
    link = data.get("Link", "")
    duplicate = check_duplicate_scheme(link)
    if duplicate:
        logger.warning(f"Duplicate URL detected for {doc_id}: {duplicate}")

        # Update schemeEntries with duplicate status
        db = firestore.client()
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update({
            "pipeline_status": "duplicate",
            "pipeline_error": f"This URL already exists: {duplicate['scheme']} ({duplicate['link']})",
            "duplicate_scheme_id": duplicate["doc_id"],
            "duplicate_scheme_name": duplicate["scheme"],
            "duplicate_normalized_url": duplicate["normalized_url"],
        })

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

        response = requests.post(
            f"{PROCESSOR_SERVICE_URL}/process",
            json={
                "doc_id": doc_id,
                "scheme_name": data.get("Scheme", "Unknown"),
                "scheme_url": data.get("Link", ""),
                "original_data": serialized_data
            },
            headers=headers,
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()

        result = response.json()
        logger.info(f"Scheme-processor result for {doc_id}: {result}")

        if not result.get("success"):
            logger.error(f"Scheme-processor failed for {doc_id}: {result.get('error')}")

    except requests.exceptions.Timeout:
        logger.error(f"Scheme-processor timeout for {doc_id}")
        _update_error_status(doc_id, "Processing timeout - service did not respond in time")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Scheme-processor connection error for {doc_id}: {e}")
        _update_error_status(doc_id, f"Could not connect to processor service: {e}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Scheme-processor error for {doc_id}: {e}")
        _update_error_status(doc_id, str(e))


def _update_error_status(doc_id: str, error_msg: str) -> None:
    """Update schemeEntries with error status."""
    try:
        db = firestore.client()
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update({
            "pipeline_status": "failed",
            "pipeline_error": error_msg,
            "pipeline_failed_at": datetime.now(timezone.utc).isoformat()
        })
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
    timeout_sec=540,  # 9 minutes max - includes waiting for Cloud Run response
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
