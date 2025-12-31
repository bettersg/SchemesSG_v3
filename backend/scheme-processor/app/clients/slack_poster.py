"""
Slack integration for posting scheme review messages.

Posts processed scheme data to Slack for human review.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.clients.slack_blocks import build_new_scheme_review_message
from loguru import logger
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient


def get_slack_client() -> Optional[WebClient]:
    """Get Slack WebClient instance."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        logger.warning("SLACK_BOT_TOKEN not configured")
        return None
    return WebClient(token=bot_token)


def get_slack_channel() -> Optional[str]:
    """Get Slack channel ID for notifications."""
    channel = os.getenv("SLACK_CHANNEL_ID")
    if not channel:
        logger.warning("SLACK_CHANNEL_ID not configured")
    return channel


def post_to_slack_for_review(doc_id: str, processed_data: Dict[str, Any], db=None) -> Optional[Dict[str, Any]]:
    """
    Post processed scheme data to Slack for human review.

    Args:
        doc_id: Document ID from schemeEntries collection
        processed_data: Result from processing pipeline
        db: Firestore client for updating slack_ts

    Returns:
        Dict with 'ok' and 'ts' if successful, None otherwise
    """
    try:
        slack_client = get_slack_client()
        channel = get_slack_channel()

        if not slack_client or not channel:
            logger.warning("Slack not configured, skipping notification")
            return None

        # Build Slack message
        message = build_new_scheme_review_message(doc_id, processed_data)

        # Post to Slack
        response = slack_client.chat_postMessage(channel=channel, **message)

        logger.info(f"Posted to Slack for {doc_id}, ts: {response.get('ts')}")

        # Store Slack message reference for later updates
        if db and response.get("ok"):
            try:
                entry_ref = db.collection("schemeEntries").document(doc_id)
                entry_ref.update(
                    {
                        "slack_channel": channel,
                        "slack_message_ts": response.get("ts"),
                        "slack_notified_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception as update_error:
                logger.warning(f"Failed to update slack_ts in Firestore: {update_error}")

        return {"ok": response.get("ok"), "ts": response.get("ts")}

    except SlackApiError as e:
        error_msg = e.response["error"] if e.response else str(e)
        logger.error(f"Slack API error for {doc_id}: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Failed to post to Slack for {doc_id}: {e}")
        return None
