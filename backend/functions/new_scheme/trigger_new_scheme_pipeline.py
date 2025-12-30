"""
Firestore Trigger for New Scheme Entries.

Triggers when a new document is created in schemeEntries collection.
Runs the processing pipeline (steps 1-4) and posts to Slack for human review.
"""
import os
import json
from datetime import datetime, timezone

from firebase_functions import firestore_fn, options
from firebase_admin import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from loguru import logger

from new_scheme.pipeline_runner import run_scheme_processing_pipeline
from new_scheme.new_scheme_blocks import (
    build_new_scheme_review_message,
    build_new_scheme_duplicate_message,
)
from new_scheme.url_utils import check_duplicate_scheme


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


@firestore_fn.on_document_created(
    document="schemeEntries/{docId}",
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,  # Need more memory for scraping/LLM
    timeout_sec=540,  # 9 minutes max for pipeline processing
)
def on_new_scheme_entry(event: firestore_fn.Event[DocumentSnapshot]) -> None:
    """
    Triggered when a new document is created in schemeEntries collection.

    Pipeline:
    1. Run scraping on submitted URL
    2. Extract LLM fields (description, eligibility, who_is_it_for, etc.)
    3. Extract planning area from address
    4. Post processed data to Slack for human review

    Skips ChromaDB/model artifact steps (5-7).
    """
    doc_id = event.params["docId"]
    data = event.data.to_dict() if event.data else {}

    logger.info(f"New scheme entry created: {doc_id}")
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

    # Check for duplicate domain
    link = data.get("Link", "")
    duplicate = check_duplicate_scheme(link)
    if duplicate:
        logger.warning(f"Duplicate domain detected for {doc_id}: {duplicate}")

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

    try:
        # Update status to processing
        db = firestore.client()
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update({
            "pipeline_status": "processing",
            "pipeline_started_at": datetime.now(timezone.utc).isoformat()
        })

        # Run the processing pipeline (steps 1-4)
        logger.info(f"Running pipeline for {doc_id}")
        processed_data = run_scheme_processing_pipeline(doc_id, data)

        # Store processed data in the document
        update_data = {
            "pipeline_status": processed_data.get("processing_status", "completed"),
            "pipeline_completed_at": datetime.now(timezone.utc).isoformat(),
            "scraped_text": processed_data.get("scraped_text", ""),
            "llm_fields": processed_data.get("llm_fields", {}),
            "planning_area": processed_data.get("planning_area"),
            "logo_url": processed_data.get("logo_url"),
        }

        if processed_data.get("error"):
            update_data["pipeline_error"] = processed_data["error"]

        entry_ref.update(update_data)
        logger.info(f"Pipeline completed for {doc_id}, status: {processed_data.get('processing_status')}")

        # Post to Slack for human review
        post_to_slack_for_review(doc_id, processed_data, entry_ref)

    except Exception as e:
        logger.error(f"Pipeline error for {doc_id}: {e}")

        # Update status to failed
        try:
            db = firestore.client()
            entry_ref = db.collection("schemeEntries").document(doc_id)
            entry_ref.update({
                "pipeline_status": "failed",
                "pipeline_error": str(e),
                "pipeline_failed_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

        # Still try to post to Slack with error info
        try:
            error_data = {
                "doc_id": doc_id,
                "scheme_name": data.get("Scheme", "Unknown"),
                "scheme_url": data.get("Link", ""),
                "scraped_text": f"Pipeline Error: {str(e)}",
                "llm_fields": {},
                "planning_area": None,
                "original_data": data,
                "processing_status": "failed",
                "error": str(e)
            }
            post_to_slack_for_review(doc_id, error_data, None)
        except Exception as slack_error:
            logger.error(f"Failed to post error to Slack: {slack_error}")


def post_to_slack_for_review(
    doc_id: str,
    processed_data: dict,
    entry_ref=None
) -> None:
    """
    Post processed scheme data to Slack for human review.

    Args:
        doc_id: Document ID from schemeEntries
        processed_data: Result from run_scheme_processing_pipeline
        entry_ref: Firestore document reference (for updating slack_ts)
    """
    try:
        slack_client = get_slack_client()
        channel = get_slack_channel()

        # Build Slack message
        message = build_new_scheme_review_message(doc_id, processed_data)

        # Post to Slack
        response = slack_client.chat_postMessage(channel=channel, **message)

        logger.info(f"Posted to Slack for {doc_id}, ts: {response.get('ts')}")

        # Store Slack message reference for later updates
        if entry_ref and response.get("ok"):
            entry_ref.update({
                "slack_channel": channel,
                "slack_message_ts": response.get("ts"),
                "slack_notified_at": datetime.now(timezone.utc).isoformat()
            })

    except SlackApiError as e:
        logger.error(f"Slack API error for {doc_id}: {e.response['error'] if e.response else str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to post to Slack for {doc_id}: {e}")
        raise


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
