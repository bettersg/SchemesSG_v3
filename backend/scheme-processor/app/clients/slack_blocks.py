"""
Slack Block Kit builders for new scheme review workflow.

Builds messages for new scheme submission notifications.
"""

from typing import Any, Dict


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length with ellipsis."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def build_scheme_review_message(
    doc_id: str,
    processed_data: Dict[str, Any],
    flavor: str = "new",
) -> dict:
    """
    Build Slack message showing processed scheme data for human review.

    The body (scraped preview, LLM fields, description) is identical for
    both flavors; only the header, context line, top section (update adds
    target ID + old URL), button labels, and summary text differ.

    Args:
        doc_id: Document ID from schemeEntries collection
        processed_data: Result from processing pipeline
        flavor: "new" for new-submission review, "update" for update-in-place

    Returns:
        Slack message payload with blocks
    """
    is_update = flavor == "update"

    scheme_name = processed_data.get("scheme_name", "(No Name)")
    scheme_url = processed_data.get("scheme_url", "")
    scraped_text = processed_data.get("scraped_text", "")
    llm_fields = processed_data.get("llm_fields", {}) or {}
    planning_area = processed_data.get("planning_area", "Not Available")
    processing_status = processed_data.get("processing_status", "unknown")
    error = processed_data.get("error")

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

    if is_update:
        target_scheme_id = processed_data.get("target_scheme_id") or "?"
        original_data = processed_data.get("original_data", {}) or {}
        old_url = original_data.get("oldLink") or original_data.get("oldUrl") or ""
        header_text = "Scheme Update — Replace Dead Link"
        top_section_text = (
            f"*{scheme_name}*  (`{target_scheme_id}`)\n"
            f"*Old URL (dead):* {old_url or '_unknown_'}\n"
            f"*Proposed URL:* <{scheme_url}|{scheme_url}>"
        )
        submitter_text = "Submitted by: automated recovery bot"
        summary_text = f"Scheme update proposal: {scheme_name} ({target_scheme_id})"
    else:
        header_text = "New Scheme Submission"
        top_section_text = f"*{scheme_name}*\n<{scheme_url}|View Original Link>"
        submitter_text = "Submitted by: Anonymous user"
        summary_text = f"New scheme submission: {scheme_name}"

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text, "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": top_section_text}},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": submitter_text},
                {"type": "mrkdwn", "text": f"{status_emoji} {status_text}"},
            ],
        },
        {"type": "divider"},
    ]

    if scraped_text and not scraped_text.startswith(("HTTP Error:", "Scraping Error:")):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Scraped Text Preview:*\n```{truncate_text(scraped_text, 400)}```",
                },
            }
        )

    def format_list_field(value) -> str:
        if isinstance(value, list):
            return ", ".join(value) if value else ""
        return str(value) if value else ""

    if llm_fields:
        fields = []

        if llm_fields.get("who_is_it_for"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Who is it for:*\n{truncate_text(format_list_field(llm_fields['who_is_it_for']), 100)}",
                }
            )

        if llm_fields.get("what_it_gives"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*What it gives:*\n{truncate_text(format_list_field(llm_fields['what_it_gives']), 100)}",
                }
            )

        if llm_fields.get("scheme_type"):
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Scheme type:*\n{truncate_text(format_list_field(llm_fields['scheme_type']), 100)}",
                }
            )

        if planning_area:
            pa_text = planning_area if isinstance(planning_area, str) else ", ".join(planning_area)
            fields.append({"type": "mrkdwn", "text": f"*Planning Area:*\n{pa_text}"})

        if fields:
            blocks.append(
                {
                    "type": "section",
                    "fields": fields[:4],
                }
            )

        if llm_fields.get("llm_description"):
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{truncate_text(llm_fields['llm_description'], 300)}",
                    },
                }
            )

    blocks.append({"type": "divider"})

    # Flavor-specific button labels. action_ids identical across flavors;
    # approval handler branches on entry's typeOfRequest, not button id.
    approve_label = "Approve Update" if is_update else "Review & Approve"
    reject_label = "Reject Update" if is_update else "Reject"

    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": approve_label, "emoji": True},
                    "style": "primary",
                    "action_id": "review_new_scheme",
                    "value": doc_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": reject_label, "emoji": True},
                    "style": "danger",
                    "action_id": "reject_new_scheme",
                    "value": doc_id,
                },
            ],
        }
    )

    return {
        "text": summary_text,
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False,
    }


def build_new_scheme_review_message(doc_id: str, processed_data: Dict[str, Any]) -> dict:
    """Backward-compatible wrapper — flavor='new'."""
    return build_scheme_review_message(doc_id, processed_data, flavor="new")


def build_scheme_update_review_message(doc_id: str, processed_data: Dict[str, Any]) -> dict:
    """Backward-compatible wrapper — flavor='update'."""
    return build_scheme_review_message(doc_id, processed_data, flavor="update")
