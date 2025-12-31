"""
Link Check and Embeddings Reindex Batch Job.

Scheduled function (runs monthly) that:
1. Checks all scheme links for dead links
2. Marks dead links as status='inactive' in Firestore
3. Posts summary to Slack
4. Reindexes Firestore embeddings (excluding inactive schemes)

Can also be run locally via:
    uv run python -c "from batch_jobs.run_link_check_and_reindex import run_link_check_and_reindex_core; run_link_check_and_reindex_core()"
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from firebase_admin import firestore
from firebase_functions import options, scheduler_fn
from loguru import logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.check_link import check_link_health
from utils.reindex_embeddings import reindex_embeddings

from batch_jobs.slack_blocks import (
    build_link_check_error_message,
    build_link_check_summary_message,
)


def get_slack_client() -> WebClient:
    """Get Slack WebClient instance."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN not set")
    return WebClient(token=bot_token)


def get_slack_channel() -> str:
    """Get Slack channel ID for notifications."""
    channel = os.getenv("SLACK_CHANNEL_ID")
    if not channel:
        raise ValueError("SLACK_CHANNEL_ID not set")
    return channel


def check_single_scheme(doc_id: str, scheme_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Check a single scheme's link health.

    Args:
        doc_id: Firestore document ID
        scheme_data: Scheme document data

    Returns:
        Tuple of (doc_id, scheme_data, check_result)
    """
    link = scheme_data.get("link", "")
    result = check_link_health(link)
    return (doc_id, scheme_data, result)


def run_link_check_and_reindex_core(db=None) -> Dict[str, Any]:
    """
    Core logic for link checking and embeddings reindex.

    This function can be called directly for local testing or from the scheduled function.

    Args:
        db: Firestore client (optional, will create if not provided)

    Returns:
        Dict with results summary
    """
    start_time = time.time()

    logger.info("Starting link check and reindex batch job...")

    try:
        if db is None:
            db = firestore.client()

        # Step 1: Fetch all schemes (including inactive - to restore if alive)
        logger.info("Fetching schemes from Firestore...")
        schemes_ref = db.collection("schemes")
        docs = schemes_ref.stream()

        schemes_to_check = []
        inactive_count = 0
        for doc in docs:
            data = doc.to_dict()
            if data.get("status") == "inactive":
                inactive_count += 1
            schemes_to_check.append((doc.id, data))

        total_count = len(schemes_to_check)
        logger.info(f"Found {total_count} schemes to check ({inactive_count} currently inactive)")

        # Step 2: Check links with concurrency
        alive_count = 0
        dead_count = 0
        restored_count = 0  # Track schemes restored from inactive
        dead_links: List[Dict[str, Any]] = []
        restored_links: List[Dict[str, Any]] = []  # Track restored schemes
        check_results: List[Tuple[str, Dict[str, Any], Dict[str, Any]]] = []

        # Use ThreadPoolExecutor for concurrent checking
        max_workers = min(20, total_count)  # Cap at 20 concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(check_single_scheme, doc_id, data): (doc_id, data) for doc_id, data in schemes_to_check
            }

            for future in as_completed(futures):
                try:
                    doc_id, scheme_data, result = future.result()
                    check_results.append((doc_id, scheme_data, result))
                    was_inactive = scheme_data.get("status") == "inactive"

                    if result["alive"]:
                        alive_count += 1
                        # Track if restoring from inactive
                        if was_inactive:
                            restored_count += 1
                            restored_links.append(
                                {
                                    "doc_id": doc_id,
                                    "scheme_name": scheme_data.get("scheme", "Unknown"),
                                    "link": scheme_data.get("link", ""),
                                    "previous_error": scheme_data.get("link_check_error", "Unknown"),
                                }
                            )
                    else:
                        dead_count += 1
                        dead_links.append(
                            {
                                "doc_id": doc_id,
                                "scheme_name": scheme_data.get("scheme", "Unknown"),
                                "link": scheme_data.get("link", ""),
                                "error": result.get("error", "Unknown"),
                                "status_code": result.get("status_code", 0),
                            }
                        )

                except Exception as e:
                    logger.error(f"Error checking scheme: {e}")
                    dead_count += 1

        logger.info(f"Link check complete: {alive_count} alive, {dead_count} dead, {restored_count} to restore")

        # Step 3: Update Firestore
        logger.info("Updating Firestore...")
        batch = db.batch()
        batch_count = 0

        for doc_id, scheme_data, result in check_results:
            scheme_ref = schemes_ref.document(doc_id)
            now_iso = datetime.now(timezone.utc).isoformat()
            was_inactive = scheme_data.get("status") == "inactive"

            if result["alive"]:
                if was_inactive:
                    # Restore inactive scheme to active (link is now alive)
                    batch.update(
                        scheme_ref,
                        {
                            "status": firestore.DELETE_FIELD,
                            "status_reason": firestore.DELETE_FIELD,
                            "status_updated_at": firestore.DELETE_FIELD,
                            "link_check_error": firestore.DELETE_FIELD,
                            "last_link_check": now_iso,
                            "link_check_status_code": result.get("status_code", 200),
                        },
                    )
                else:
                    # Update last check timestamp for alive links
                    batch.update(
                        scheme_ref,
                        {"last_link_check": now_iso, "link_check_status_code": result.get("status_code", 200)},
                    )
            else:
                # Mark dead links as inactive
                batch.update(
                    scheme_ref,
                    {
                        "status": "inactive",
                        "status_reason": "Dead link detected",
                        "status_updated_at": now_iso,
                        "last_link_check": now_iso,
                        "link_check_status_code": result.get("status_code", 0),
                        "link_check_error": result.get("error", "Unknown"),
                    },
                )

            batch_count += 1

            # Commit in batches of 500 (Firestore limit)
            if batch_count >= 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0

        # Commit remaining
        if batch_count > 0:
            batch.commit()

        logger.info("Firestore updates complete")

        # Step 4: Reindex Firestore embeddings
        logger.info("Reindexing Firestore embeddings...")
        reindex_result = reindex_embeddings(db)

        # Calculate duration
        end_time = time.time()
        duration_seconds = round(end_time - start_time, 2)

        # Step 5: Post to Slack
        logger.info("Posting summary to Slack...")
        try:
            slack_client = get_slack_client()
            channel = get_slack_channel()

            results_summary = {
                "total_checked": total_count,
                "alive_count": alive_count,
                "dead_count": dead_count,
                "restored_count": restored_count,
                "duration_seconds": duration_seconds,
            }

            message = build_link_check_summary_message(results_summary, dead_links, reindex_result, restored_links)

            slack_client.chat_postMessage(channel=channel, **message)
            logger.info("Slack notification sent")

        except (SlackApiError, ValueError) as e:
            logger.error(f"Failed to send Slack notification: {e}")

        # Return summary
        response_data = {
            "success": True,
            "link_check": {
                "total_checked": total_count,
                "alive_count": alive_count,
                "dead_count": dead_count,
                "restored_count": restored_count,
                "dead_links": dead_links,
                "restored_links": restored_links,
            },
            "reindex": reindex_result,
            "duration_seconds": duration_seconds,
        }

        logger.info(f"Batch job complete in {duration_seconds}s")
        return response_data

    except Exception as e:
        logger.error(f"Batch job failed: {e}")

        # Try to send error notification to Slack
        try:
            slack_client = get_slack_client()
            channel = get_slack_channel()
            error_message = build_link_check_error_message(str(e))
            slack_client.chat_postMessage(channel=channel, **error_message)
        except Exception:
            pass

        return {"success": False, "error": str(e)}


@scheduler_fn.on_schedule(
    schedule="0 9 1 * *",  # Run at 9am on the 1st of every month
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
    timeout_sec=540,  # 9 minutes max
    retry_count=1,
)
def scheduled_link_check_and_reindex(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Monthly scheduled function for link checking and embeddings reindex.

    Runs on the 1st of every month at 9am SGT.
    Checks all scheme links, marks dead ones as inactive, and reindexes embeddings.

    Args:
        event: Scheduled event object from Firebase
    """
    logger.info(f"Scheduled job triggered at {event.schedule_time}")
    result = run_link_check_and_reindex_core()
    logger.info(f"Scheduled job result: {json.dumps(result, default=str)}")
