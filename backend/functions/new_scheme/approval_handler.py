"""
Approval Handler for New Scheme Submissions.

Handles Slack modal submissions to approve/reject new schemes:
- Extracts form data from modal state
- Creates new document in schemes collection (on approval)
- Updates schemeEntries document with status
- Posts confirmation message to Slack
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from firebase_admin import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
from loguru import logger
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from new_scheme.new_scheme_blocks import (
    build_new_scheme_approved_message,
    build_new_scheme_rejected_message,
)


def handle_new_scheme_approval(
    slack_client: WebClient,
    event: dict,
    entry_doc_id: str,
) -> dict:
    """
    Handle approval of new scheme from Slack modal submission.

    Args:
        slack_client: Slack WebClient instance
        event: Slack view_submission event
        entry_doc_id: Document ID from schemeEntries collection

    Returns:
        Response dict for Slack (e.g., {"response_action": "clear"})
    """
    view = event.get("view", {})
    metadata_raw = view.get("private_metadata", "{}")

    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError:
        metadata = {"doc_id": entry_doc_id}

    channel_id = metadata.get("channel")
    message_ts = metadata.get("message_ts")
    reviewer_id = event.get("user", {}).get("id", "")
    reviewed_at = datetime.now(timezone.utc).isoformat()

    # Extract form values from modal state
    state = view.get("state", {}).get("values", {})
    approved_data = extract_form_data(state)

    # Get original pipeline results to include fields not shown in Slack form
    original_data = get_processed_data_from_entry(entry_doc_id)
    original_llm_fields = original_data.get("llm_fields", {})

    # Merge: form data takes precedence, but include LLM-only fields
    llm_only_fields = ["summary", "search_booster", "service_area"]
    for field in llm_only_fields:
        if field not in approved_data or not approved_data.get(field):
            approved_data[field] = original_llm_fields.get(field)

    logger.info(f"Processing approval for entry {entry_doc_id}")

    try:
        db = firestore.client()

        # Get reviewer email from Slack
        reviewer_email = None
        try:
            user_info = slack_client.users_info(user=reviewer_id)
            if user_info.get("ok"):
                reviewer_email = user_info.get("user", {}).get("profile", {}).get("email")
        except Exception as e:
            logger.warning(f"Could not get reviewer email from Slack: {e}")

        # Create new document in schemes collection
        schemes_ref = db.collection("schemes").document()
        scheme_data = {
            **approved_data,
            "approved_by": reviewer_email or reviewer_id,
            "approved_at": SERVER_TIMESTAMP,
            "source_entry_id": entry_doc_id,
            "created_at": SERVER_TIMESTAMP,
            "status": "active",
            "scraped_text": original_data.get("scraped_text", ""),
            "last_llm_processed_update": SERVER_TIMESTAMP,
            "last_scraped_update": SERVER_TIMESTAMP,
        }

        # Rename some fields to match schemes collection schema
        if "scheme_name" in scheme_data:
            scheme_data["scheme"] = scheme_data.pop("scheme_name")
        if "scheme_url" in scheme_data:
            scheme_data["link"] = scheme_data.pop("scheme_url")
        if "llm_description" in scheme_data:
            scheme_data["description"] = scheme_data.get("llm_description", "")
        if "image_url" in scheme_data:
            scheme_data["image"] = scheme_data.pop("image_url")

        schemes_ref.set(scheme_data)
        new_scheme_id = schemes_ref.id

        logger.info(f"Created new scheme document: {new_scheme_id}")

        # Update schemeEntries document with approved data
        entries_ref = db.collection("schemeEntries").document(entry_doc_id)
        entries_ref.update(
            {
                "Status": "approved",
                "approved_by": reviewer_email or reviewer_id,
                "approved_at": SERVER_TIMESTAMP,
                "approved_scheme_id": new_scheme_id,
                # Store the reviewed/edited data
                "reviewed_data": approved_data,
                "Scheme": approved_data.get("scheme_name"),
                "Link": approved_data.get("scheme_url"),
                "llm_fields": {
                    "who_is_it_for": approved_data.get("who_is_it_for", []),
                    "what_it_gives": approved_data.get("what_it_gives", []),
                    "scheme_type": approved_data.get("scheme_type", []),
                    "llm_description": approved_data.get("llm_description"),
                    "summary": approved_data.get("summary"),
                    "eligibility": approved_data.get("eligibility"),
                    "how_to_apply": approved_data.get("how_to_apply"),
                    "agency": approved_data.get("agency"),
                    "address": approved_data.get("address"),
                    "phone": approved_data.get("phone"),
                    "email": approved_data.get("email"),
                    "service_area": approved_data.get("service_area"),
                    "search_booster": approved_data.get("search_booster"),
                },
                "planning_area": approved_data.get("planning_area"),
                "logo_url": approved_data.get("image_url"),
            }
        )

        logger.info(f"Updated schemeEntries {entry_doc_id} with approval status")

        # Update original Slack message
        if channel_id and message_ts:
            try:
                approved_message = build_new_scheme_approved_message(
                    doc_id=entry_doc_id,
                    scheme_name=approved_data.get("scheme_name", "Unknown"),
                    scheme_url=approved_data.get("scheme_url", ""),
                    reviewer_id=reviewer_id,
                    reviewed_at=reviewed_at,
                    new_scheme_id=new_scheme_id,
                )
                slack_client.chat_update(channel=channel_id, ts=message_ts, **approved_message)
            except SlackApiError as e:
                logger.error(f"Failed to update Slack message: {e}")

        # Post thank you message
        if channel_id:
            try:
                thank_text = (
                    f"Thank you <@{reviewer_id}>! New scheme *{approved_data.get('scheme_name', 'Unknown')}* "
                    f"has been added to the database (ID: `{new_scheme_id}`)."
                )
                slack_client.chat_postMessage(channel=channel_id, text=thank_text)
            except SlackApiError:
                pass

        return {"response_action": "clear"}

    except Exception as e:
        logger.error(f"Error approving scheme {entry_doc_id}: {e}")

        # Return error to Slack modal
        return {"response_action": "errors", "errors": {"scheme_name_block": f"Error saving scheme: {str(e)}"}}


def handle_new_scheme_rejection(
    slack_client: WebClient,
    entry_doc_id: str,
    channel_id: Optional[str],
    message_ts: Optional[str],
    reviewer_id: str,
    reason: Optional[str] = None,
) -> None:
    """
    Handle rejection of new scheme submission.

    Args:
        slack_client: Slack WebClient instance
        entry_doc_id: Document ID from schemeEntries collection
        channel_id: Slack channel ID
        message_ts: Original message timestamp
        reviewer_id: Slack user ID of reviewer
        reason: Optional rejection reason
    """
    logger.info(f"Processing rejection for entry {entry_doc_id}")

    try:
        db = firestore.client()

        # Get scheme name from entry
        entry_ref = db.collection("schemeEntries").document(entry_doc_id)
        entry_doc = entry_ref.get()

        scheme_name = "Unknown"
        if entry_doc.exists:
            entry_data = entry_doc.to_dict()
            scheme_name = entry_data.get("Scheme", entry_data.get("scheme_name", "Unknown"))

            # Update schemeEntries document
            entry_ref.update(
                {
                    "Status": "rejected",
                    "rejected_by": reviewer_id,
                    "rejected_at": SERVER_TIMESTAMP,
                    "rejection_reason": reason,
                }
            )

        # Update original Slack message
        if channel_id and message_ts:
            try:
                rejected_message = build_new_scheme_rejected_message(
                    doc_id=entry_doc_id, scheme_name=scheme_name, reviewer_id=reviewer_id, reason=reason
                )
                slack_client.chat_update(channel=channel_id, ts=message_ts, **rejected_message)
            except SlackApiError as e:
                logger.error(f"Failed to update Slack message: {e}")

    except Exception as e:
        logger.error(f"Error rejecting scheme {entry_doc_id}: {e}")


def extract_form_data(state: dict) -> Dict[str, Any]:
    """
    Extract form data from Slack modal state.

    Args:
        state: Modal state values dict

    Returns:
        Dict with extracted form values
    """

    def get_value(block_id: str, action_id: str) -> Optional[str]:
        """Get text input value from state."""
        block = state.get(block_id, {})
        action = block.get(action_id, {})
        return action.get("value", "")

    def get_multi_select_as_string(block_id: str, action_id: str) -> str:
        """Get multi-select values as comma-separated string."""
        block = state.get(block_id, {})
        action = block.get(action_id, {})
        selected = action.get("selected_options", [])
        values = [opt.get("value", "") for opt in selected if opt.get("value")]
        return ", ".join(values) if values else ""

    return {
        "scheme_name": get_value("scheme_name_block", "scheme_name"),
        "scheme_url": get_value("scheme_url_block", "scheme_url"),
        "agency": get_value("agency_block", "agency"),
        "image_url": get_value("image_url_block", "image_url"),
        "address": get_value("address_block", "address"),
        "phone": get_value("phone_block", "phone"),
        "email": get_value("email_block", "email"),
        "planning_area": get_value("planning_area_block", "planning_area"),
        "who_is_it_for": get_multi_select_as_string("who_is_it_for_block", "who_is_it_for"),
        "what_it_gives": get_multi_select_as_string("what_it_gives_block", "what_it_gives"),
        "scheme_type": get_multi_select_as_string("scheme_type_block", "scheme_type"),
        "llm_description": get_value("llm_description_block", "llm_description"),
        "eligibility": get_value("eligibility_block", "eligibility"),
        "how_to_apply": get_value("how_to_apply_block", "how_to_apply"),
    }


def get_processed_data_from_entry(entry_doc_id: str) -> Dict[str, Any]:
    """
    Get processed data from schemeEntries document.

    Args:
        entry_doc_id: Document ID from schemeEntries collection

    Returns:
        Processed data dict for modal pre-filling
    """
    try:
        db = firestore.client()
        entry_ref = db.collection("schemeEntries").document(entry_doc_id)
        entry_doc = entry_ref.get()

        if not entry_doc.exists:
            logger.warning(f"Entry not found: {entry_doc_id}")
            return {}

        data = entry_doc.to_dict()

        return {
            "doc_id": entry_doc_id,
            "scheme_name": data.get("Scheme", data.get("scheme_name", "")),
            "scheme_url": data.get("Link", data.get("link", "")),
            "scraped_text": data.get("scraped_text", ""),
            "llm_fields": data.get("llm_fields", {}),
            "planning_area": data.get("planning_area"),
            "logo_url": data.get("logo_url"),
            "original_data": data,
            "processing_status": data.get("pipeline_status", "unknown"),
            "error": data.get("pipeline_error"),
        }

    except Exception as e:
        logger.error(f"Error getting processed data for {entry_doc_id}: {e}")
        return {}
