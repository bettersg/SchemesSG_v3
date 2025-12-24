"""
Slack integration Firebase Functions.

This module provides Firebase Functions for Slack integration including:
- Triggering review messages
- Scanning and notifying about new scraping errors
- Handling Slack interactive components (buttons, modals)
"""
import json
import os
import urllib.parse
import traceback
from datetime import datetime, timezone

from firebase_functions import https_fn, options
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from loguru import logger

from slack_integration.block_kit import build_review_message, build_review_modal, build_review_locked_message
from slack_integration.slack_utils import verify_slack_signature
from slack_integration.storage import (
    read_source_rows,
    load_notified_ids,
    save_notified_ids,
    get_source_doc,
    upsert_edit_doc,
    upsert_source_doc,
)


def get_slack_client() -> WebClient:
    """
    Get Slack WebClient instance.
    
    Returns:
        WebClient instance configured with bot token from environment
    """
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")
    return WebClient(token=bot_token)


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
)
def slack_trigger_message(req: https_fn.Request) -> https_fn.Response:
    """
    Trigger a Slack review message for a specific document.
    
    Creates or updates a source document in Firestore and posts a review message to Slack.
    
    Args:
        req: Firebase Function request object
        
    Returns:
        Response with success status and doc_id
    """
    headers = {"Content-Type": "application/json"}
    
    if req.method != "POST":
        return https_fn.Response(
            response=json.dumps({"error": "Only POST requests are allowed"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )
    
    try:
        body = req.get_json(silent=True) or {}
        channel = body.get("channel") or os.getenv("SLACK_CHANNEL_ID")
        
        if not channel:
            return https_fn.Response(
                response=json.dumps({"error": "Set SLACK_CHANNEL_ID or pass {\"channel\": \"C...\"}"}),
                status=400,
                mimetype="application/json",
                headers=headers,
            )
        
        doc_id = body.get("doc_id") or "test-doc"
        data = {
            "scheme_name": body.get("scheme_name", "Test Scheme"),
            "scheme_url": body.get("scheme_url", "https://example.com"),
            "scraped_text": body.get("scraped_text", ""),
            # New fields for enhanced modal
            "agency": body.get("agency", ""),
            "image_url": body.get("image_url", ""),
            "phone": body.get("phone", ""),
            "address": body.get("address", ""),
            "who_is_it_for": body.get("who_is_it_for", ""),
            "what_it_gives": body.get("what_it_gives", ""),
            "scheme_type": body.get("scheme_type", ""),
            "llm_description": body.get("llm_description", body.get("scraped_text", "")),
            "eligibility": body.get("eligibility", ""),
            "how_to_apply": body.get("how_to_apply", ""),
        }
        
        # Upsert source document to Firestore
        upsert_source_doc(doc_id, data)
        
        # Build and send Slack message
        payload = build_review_message(doc_id, data)
        slack_client = get_slack_client()
        
        try:
            slack_client.chat_postMessage(channel=channel, **payload)
        except SlackApiError as e:
            return https_fn.Response(
                response=json.dumps({
                    "error": str(e),
                    "details": e.response.data if e.response else None
                }),
                status=500,
                mimetype="application/json",
                headers=headers,
            )
        
        return https_fn.Response(
            response=json.dumps({"ok": True, "doc_id": doc_id}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )
        
    except Exception as e:
        return https_fn.Response(
            response=json.dumps({"error": f"Internal server error: {str(e)}"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
    timeout_sec=540,  # 9 minutes max for batch processing
)
def slack_scan_and_notify(req: https_fn.Request) -> https_fn.Response:
    """
    Scan source documents and post review messages for new items.
    
    Reads all source documents from Firestore, filters out already notified ones,
    and posts Slack messages for new documents.
    
    Args:
        req: Firebase Function request object
        
    Returns:
        Response with list of posted document IDs
    """
    headers = {"Content-Type": "application/json"}
    
    if req.method != "POST":
        return https_fn.Response(
            response=json.dumps({"error": "Only POST requests are allowed"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )
    
    try:
        body = req.get_json(silent=True) or {}
        channel = body.get("channel") or os.getenv("SLACK_CHANNEL_ID")
        
        if not channel:
            return https_fn.Response(
                response=json.dumps({"error": "Set SLACK_CHANNEL_ID or pass {\"channel\": \"C...\"}"}),
                status=400,
                mimetype="application/json",
                headers=headers,
            )
        
        # Read all source rows from Firestore
        rows = read_source_rows()
        notified = load_notified_ids()
        posted = []
        
        slack_client = get_slack_client()
        
        for row in rows:
            doc_id = row.get("id")
            if not doc_id or doc_id in notified:
                continue
            
            # Build data object with all fields matching slack_trigger_message
            data = {
                "scheme_name": row.get("scheme_name", ""),
                "scheme_url": row.get("scheme_url", ""),
                "scraped_text": row.get("scraped_text", ""),
                # Enhanced fields for full data model
                "agency": row.get("agency", ""),
                "image_url": row.get("image_url", ""),
                "phone": row.get("phone", ""),
                "address": row.get("address", ""),
                "who_is_it_for": row.get("who_is_it_for", ""),
                "what_it_gives": row.get("what_it_gives", ""),
                "scheme_type": row.get("scheme_type", ""),
                "llm_description": row.get("llm_description", row.get("scraped_text", "")),
                "eligibility": row.get("eligibility", ""),
                "how_to_apply": row.get("how_to_apply", ""),
            }
            
            payload = build_review_message(doc_id, data)
            try:
                slack_client.chat_postMessage(channel=channel, **payload)
                posted.append(doc_id)
            except SlackApiError:
                # Continue with next item, but don't mark as posted
                pass
        
        # Save notified IDs to Firestore
        if posted:
            notified.update(posted)
            save_notified_ids(notified)
        
        return https_fn.Response(
            response=json.dumps({"ok": True, "posted": posted}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )
        
    except Exception as e:
        return https_fn.Response(
            response=json.dumps({"error": f"Internal server error: {str(e)}"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
)
def slack_interactive(req: https_fn.Request) -> https_fn.Response:
    """
    Handle Slack interactive component events (button clicks, modal submissions).
    
    This endpoint handles:
    - block_actions: Button clicks that open modals
    - view_submission: Modal form submissions
    
    Args:
        req: Firebase Function request object (contains form-encoded data from Slack)
        
    Returns:
        Response appropriate for Slack interactive component protocol
    """
    # Slack interactive endpoints don't need CORS headers
    headers = {"Content-Type": "application/json"}
    
    if req.method != "POST":
        return https_fn.Response(
            response="",
            status=405,
            headers=headers,
        )
    
    # Verify Slack signature
    if not verify_slack_signature(req):
        return https_fn.Response(
            response="",
            status=401,
            headers=headers,
        )
    
    try:
        # Parse form-encoded data from Slack
        # Slack sends application/x-www-form-urlencoded, not JSON
        content_type = req.headers.get("Content-Type", "")
        
        if "application/x-www-form-urlencoded" in content_type:
            body_str = req.get_data().decode("utf-8")
            form_data = urllib.parse.parse_qs(body_str)
            payload_str = form_data.get("payload", [None])[0]
            
            if not payload_str:
                return https_fn.Response(
                    response="",
                    status=400,
                    headers=headers,
                )
            
            event = json.loads(payload_str)
        else:
            # Fallback to JSON (for testing)
            event = req.get_json() or {}
        
        etype = event.get("type")
        slack_client = get_slack_client()
        
        # Handle button clicks (block_actions)
        if etype == "block_actions":
            actions = event.get("actions", [])
            if not actions:
                return https_fn.Response(
                    response="",
                    status=200,
                    headers=headers,
                )
            
            action = actions[0]
            if action.get("action_id") == "review_scheme":
                doc_id = action.get("value")
                trigger_id = event.get("trigger_id")
                
                # Get existing source document from Firestore
                existing = get_source_doc(doc_id) or {}
                data = {
                    "scheme_name": existing.get("scheme_name", ""),
                    "scheme_url": existing.get("scheme_url", ""),
                    "agency": existing.get("agency", ""),
                    "image_url": existing.get("image_url", ""),
                    "phone": existing.get("phone", ""),
                    "address": existing.get("address", ""),
                    "who_is_it_for": existing.get("who_is_it_for", ""),
                    "what_it_gives": existing.get("what_it_gives", ""),
                    "scheme_type": existing.get("scheme_type", ""),
                    "llm_description": existing.get("llm_description", existing.get("scraped_text", "")),
                    "eligibility": existing.get("eligibility", ""),
                    "how_to_apply": existing.get("how_to_apply", ""),
                }
                
                # Build metadata for modal
                container = event.get("container", {})
                metadata = {
                    "doc_id": doc_id,
                    "channel": container.get("channel_id"),
                    "message_ts": container.get("message_ts"),
                }
                
                # Open modal
                logger.info(f"Opening modal for doc_id={doc_id}")
                modal_view = build_review_modal(json.dumps(metadata), data)
                try:
                    result = slack_client.views_open(trigger_id=trigger_id, view=modal_view)
                    logger.info(f"Modal opened successfully: {result.get('ok', False)}")
                except SlackApiError as e:
                    logger.error(f"Failed to open modal: {e.response['error'] if e.response else str(e)}")
                    logger.debug(f"Modal view structure: {json.dumps(modal_view, indent=2)}")
                    logger.debug(traceback.format_exc())
                    # Still return 200 to prevent Slack from retrying
                
                return https_fn.Response(
                    response="",
                    status=200,
                    headers=headers,
                )
            
            return https_fn.Response(
                response="",
                status=200,
                headers=headers,
            )
        
        # Handle modal submissions (view_submission)
        if etype == "view_submission":
            view = event.get("view", {})
            metadata_raw = view.get("private_metadata") or "{}"
            
            try:
                metadata = json.loads(metadata_raw)
            except json.JSONDecodeError:
                metadata = {"doc_id": metadata_raw}
            
            doc_id = metadata.get("doc_id", "")
            channel_id = metadata.get("channel")
            message_ts = metadata.get("message_ts")
            
            # Get existing document to preserve scheme_url
            existing = get_source_doc(doc_id) or {}
            
            # Extract form values from modal state
            state = view.get("state", {}).get("values", {})
            
            # Pre-filled text fields
            scheme_name = state.get("scheme_name_block", {}).get("scheme_name", {}).get("value", "")
            agency = state.get("agency_block", {}).get("agency", {}).get("value", "")
            image_url = state.get("image_url_block", {}).get("image_url", {}).get("value", "")
            phone = state.get("phone_block", {}).get("phone", {}).get("value", "")
            address = state.get("address_block", {}).get("address", {}).get("value", "")
            
            # Dropdowns
            who_is_it_for_obj = state.get("who_is_it_for_block", {}).get("who_is_it_for", {})
            who_is_it_for = who_is_it_for_obj.get("selected_option", {}).get("value", "") if who_is_it_for_obj.get("selected_option") else ""
            
            what_it_gives_obj = state.get("what_it_gives_block", {}).get("what_it_gives", {})
            what_it_gives = what_it_gives_obj.get("selected_option", {}).get("value", "") if what_it_gives_obj.get("selected_option") else ""
            
            scheme_type_obj = state.get("scheme_type_block", {}).get("scheme_type", {})
            scheme_type = scheme_type_obj.get("selected_option", {}).get("value", "") if scheme_type_obj.get("selected_option") else ""
            
            # Text areas
            llm_description = state.get("llm_description_block", {}).get("llm_description", {}).get("value", "")
            eligibility = state.get("eligibility_block", {}).get("eligibility", {}).get("value", "")
            how_to_apply = state.get("how_to_apply_block", {}).get("how_to_apply", {}).get("value", "")
            
            reviewer_id = event.get("user", {}).get("id", "")
            reviewed_at = datetime.now(timezone.utc).isoformat()
            
            # Save edited document to Firestore
            upsert_edit_doc(
                doc_id,
                {
                    "scheme_name": scheme_name,
                    "scheme_url": existing.get("scheme_url", ""),  # URL not in modal but should be preserved
                    "agency": agency,
                    "image_url": image_url,
                    "phone": phone,
                    "address": address,
                    "who_is_it_for": who_is_it_for,
                    "what_it_gives": what_it_gives,
                    "scheme_type": scheme_type,
                    "llm_description": llm_description,
                    "eligibility": eligibility,
                    "how_to_apply": how_to_apply,
                    "updated_by": reviewer_id,
                    "updated_at": reviewed_at,
                },
            )
            
            updated_data = {
                "scheme_name": scheme_name,
                "scheme_url": existing.get("scheme_url", ""),
                "agency": agency,
                "image_url": image_url,
                "phone": phone,
                "address": address,
                "who_is_it_for": who_is_it_for,
                "what_it_gives": what_it_gives,
                "scheme_type": scheme_type,
                "llm_description": llm_description,
                "eligibility": eligibility,
                "how_to_apply": how_to_apply,
            }
            
            # Update the original message to show it's reviewed
            if channel_id and message_ts:
                locked_message = build_review_locked_message(doc_id, updated_data, reviewer_id, reviewed_at)
                try:
                    slack_client.chat_update(channel=channel_id, ts=message_ts, **locked_message)
                except SlackApiError:
                    pass
            
            # Post thank you message
            if channel_id and reviewer_id:
                thank_text = (
                    f"Thank you for your contribution, <@{reviewer_id}>! "
                    f"Scheme: *{scheme_name or '(no name)'}* (ID: `{doc_id}`)"
                )
                try:
                    slack_client.chat_postMessage(channel=channel_id, text=thank_text)
                except SlackApiError:
                    pass
            
            # Return response action to close modal
            return https_fn.Response(
                response=json.dumps({"response_action": "clear"}),
                status=200,
                mimetype="application/json",
                headers=headers,
            )
        
        # Unknown event type
        return https_fn.Response(
            response="",
            status=200,
            headers=headers,
        )
        
    except Exception as e:
        return https_fn.Response(
            response="",
            status=500,
            headers=headers,
        )

