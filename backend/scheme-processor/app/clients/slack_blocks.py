"""
Slack Block Kit builders for new scheme review workflow.

Builds messages for new scheme submission notifications.
"""
from typing import Dict, Any, List

from app.constants import WHO_IS_IT_FOR, WHAT_IT_GIVES, SCHEME_TYPE


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length with ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def build_new_scheme_review_message(doc_id: str, processed_data: Dict[str, Any]) -> dict:
    """
    Build Slack message showing processed scheme data for human review.

    Args:
        doc_id: Document ID from schemeEntries collection
        processed_data: Result from processing pipeline

    Returns:
        Slack message payload with blocks
    """
    scheme_name = processed_data.get("scheme_name", "(No Name)")
    scheme_url = processed_data.get("scheme_url", "")
    scraped_text = processed_data.get("scraped_text", "")
    llm_fields = processed_data.get("llm_fields", {})
    planning_area = processed_data.get("planning_area", "Not Available")
    processing_status = processed_data.get("processing_status", "unknown")
    error = processed_data.get("error")

    # Build status indicator
    if processing_status == "completed":
        status_emoji = ":white_check_mark:"
        status_text = "Pipeline completed successfully"
    elif processing_status == "scraping_failed":
        status_emoji = ":warning:"
        status_text = f"Scraping failed: {error}"
    elif processing_status == "needs_review":
        status_emoji = ":eyes:"
        status_text = f"Needs manual review: {error}"
    else:
        status_emoji = ":x:"
        status_text = f"Processing failed: {error}"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "New Scheme Submission", "emoji": True}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{scheme_name}*\n<{scheme_url}|View Original Link>"
            }
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Submitted by: Anonymous user"},
                {"type": "mrkdwn", "text": f"{status_emoji} {status_text}"}
            ]
        },
        {"type": "divider"},
    ]

    # Add scraped text preview if available
    if scraped_text and not scraped_text.startswith(("HTTP Error:", "Scraping Error:")):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Scraped Text Preview:*\n```{truncate_text(scraped_text, 400)}```"
            }
        })

    def format_list_field(value) -> str:
        """Format a list field for display."""
        if isinstance(value, list):
            return ", ".join(value) if value else ""
        return str(value) if value else ""

    # Add LLM extracted fields
    if llm_fields:
        fields = []

        if llm_fields.get("who_is_it_for"):
            fields.append({
                "type": "mrkdwn",
                "text": f"*Who is it for:*\n{truncate_text(format_list_field(llm_fields['who_is_it_for']), 100)}"
            })

        if llm_fields.get("what_it_gives"):
            fields.append({
                "type": "mrkdwn",
                "text": f"*What it gives:*\n{truncate_text(format_list_field(llm_fields['what_it_gives']), 100)}"
            })

        if llm_fields.get("scheme_type"):
            fields.append({
                "type": "mrkdwn",
                "text": f"*Scheme type:*\n{truncate_text(format_list_field(llm_fields['scheme_type']), 100)}"
            })

        if planning_area:
            pa_text = planning_area if isinstance(planning_area, str) else ", ".join(planning_area)
            fields.append({
                "type": "mrkdwn",
                "text": f"*Planning Area:*\n{pa_text}"
            })

        if fields:
            blocks.append({
                "type": "section",
                "fields": fields[:4]  # Slack allows max 10 fields, we use 4
            })

        # Add description preview
        if llm_fields.get("llm_description"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{truncate_text(llm_fields['llm_description'], 300)}"
                }
            })

    blocks.append({"type": "divider"})

    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Review & Approve", "emoji": True},
                "style": "primary",
                "action_id": "review_new_scheme",
                "value": doc_id
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                "style": "danger",
                "action_id": "reject_new_scheme",
                "value": doc_id
            }
        ]
    })

    return {
        "text": f"New scheme submission: {scheme_name}",
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False
    }
