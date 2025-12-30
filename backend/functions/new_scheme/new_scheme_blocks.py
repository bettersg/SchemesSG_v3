"""
Slack Block Kit builders for new scheme review workflow.

Builds messages and modals for:
- New scheme submission notifications
- Processed scheme review with LLM fields
- Approval confirmation messages
"""
from typing import Dict, Any, Optional, List

from new_scheme.pipeline_runner import WHO_IS_IT_FOR, WHAT_IT_GIVES, SCHEME_TYPE


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
        processed_data: Result from run_scheme_processing_pipeline

    Returns:
        Slack message payload with blocks
    """
    scheme_name = processed_data.get("scheme_name", "(No Name)")
    scheme_url = processed_data.get("scheme_url", "")
    scraped_text = processed_data.get("scraped_text", "")
    llm_fields = processed_data.get("llm_fields", {})
    planning_area = processed_data.get("planning_area", "Not Available")
    original_data = processed_data.get("original_data", {})
    processing_status = processed_data.get("processing_status", "unknown")
    error = processed_data.get("error")

    # New scheme submissions are from anonymous users (public form)
    # Don't display user info that may be test data

    # Build status indicator
    if processing_status == "completed":
        status_emoji = ":white_check_mark:"
        status_text = "Pipeline completed successfully"
    elif processing_status == "scraping_failed":
        status_emoji = ":warning:"
        status_text = f"Scraping failed: {error}"
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


def build_new_scheme_review_modal(metadata: str, processed_data: Dict[str, Any]) -> dict:
    """
    Build review modal form for approving new scheme.

    Pre-fills with LLM extracted data, allows admin to edit before approval.

    Args:
        metadata: JSON string with doc_id, channel, message_ts
        processed_data: Result from run_scheme_processing_pipeline

    Returns:
        Slack modal view payload
    """
    llm_fields = processed_data.get("llm_fields", {})
    original_data = processed_data.get("original_data", {})

    scheme_name = processed_data.get("scheme_name", original_data.get("Scheme", ""))
    scheme_url = processed_data.get("scheme_url", original_data.get("Link", ""))
    logo_url = processed_data.get("logo_url", "")
    planning_area = processed_data.get("planning_area", "")

    # Get LLM extracted values
    llm_description = llm_fields.get("llm_description", "") or ""
    eligibility = llm_fields.get("eligibility", "") or ""
    how_to_apply = llm_fields.get("how_to_apply", "") or ""
    who_is_it_for = llm_fields.get("who_is_it_for", "") or ""
    what_it_gives = llm_fields.get("what_it_gives", "") or ""
    scheme_type = llm_fields.get("scheme_type", "") or ""
    address = llm_fields.get("address", "") or ""
    phone = llm_fields.get("phone", "") or ""
    email = llm_fields.get("email", "") or ""

    # Handle list values - convert to comma-separated strings
    if isinstance(address, list):
        address = ", ".join(str(a) for a in address if a)
    if isinstance(phone, list):
        phone = ", ".join(str(p) for p in phone if p)
    if isinstance(email, list):
        email = ", ".join(str(e) for e in email if e)
    if isinstance(planning_area, list):
        planning_area = ", ".join(str(p) for p in planning_area if p)
    if isinstance(who_is_it_for, list):
        who_is_it_for = ", ".join(str(w) for w in who_is_it_for if w)
    if isinstance(what_it_gives, list):
        what_it_gives = ", ".join(str(w) for w in what_it_gives if w)
    if isinstance(scheme_type, list):
        scheme_type = ", ".join(str(s) for s in scheme_type if s)
    if isinstance(llm_description, list):
        llm_description = " ".join(str(d) for d in llm_description if d)
    if isinstance(eligibility, list):
        eligibility = " ".join(str(e) for e in eligibility if e)
    if isinstance(how_to_apply, list):
        how_to_apply = " ".join(str(h) for h in how_to_apply if h)

    # Build multi-select options from constants
    who_is_it_for_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]}
        for opt in WHO_IS_IT_FOR
    ]

    what_it_gives_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]}
        for opt in WHAT_IT_GIVES
    ]

    scheme_type_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]}
        for opt in SCHEME_TYPE
    ]

    def get_initial_options(llm_value: str, options: List[dict]) -> List[dict]:
        """Get initial options that match comma-separated LLM values."""
        if not llm_value:
            return []

        # Parse comma-separated string into list
        values = [v.strip() for v in llm_value.split(",") if v.strip()]

        matched = []
        for opt in options:
            if opt["value"] in values:
                matched.append(opt)

        return matched[:10]  # Slack limit

    blocks = [
        # Basic Information Section
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Basic Information"}
        },
        {
            "type": "input",
            "block_id": "scheme_name_block",
            "label": {"type": "plain_text", "text": "Scheme Name"},
            "element": {
                "type": "plain_text_input",
                "action_id": "scheme_name",
                "initial_value": str(scheme_name)[:150]
            }
        },
        {
            "type": "input",
            "block_id": "scheme_url_block",
            "label": {"type": "plain_text", "text": "Scheme URL"},
            "element": {
                "type": "plain_text_input",
                "action_id": "scheme_url",
                "initial_value": str(scheme_url)[:500]
            }
        },
    ]

    # Add image preview if logo_url is a valid absolute URL
    if logo_url and str(logo_url).startswith(("http://", "https://")):
        blocks.append({
            "type": "image",
            "block_id": "image_preview_block",
            "image_url": str(logo_url)[:2000],
            "alt_text": "Scheme logo"
        })

    blocks.extend([
        {
            "type": "input",
            "block_id": "image_url_block",
            "label": {"type": "plain_text", "text": "Logo/Image URL"},
            "element": {
                "type": "plain_text_input",
                "action_id": "image_url",
                "initial_value": str(logo_url)[:500] if logo_url else ""
            },
            "optional": True
        },
        {
            "type": "actions",
            "block_id": "image_preview_actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Preview Image", "emoji": True},
                    "action_id": "preview_image_button"
                }
            ]
        },

        # Contact Information Section
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Contact Information"}
        },
        {
            "type": "input",
            "block_id": "address_block",
            "label": {"type": "plain_text", "text": "Address"},
            "element": {
                "type": "plain_text_input",
                "action_id": "address",
                "initial_value": str(address)[:500],
                "multiline": True
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "phone_block",
            "label": {"type": "plain_text", "text": "Phone"},
            "element": {
                "type": "plain_text_input",
                "action_id": "phone",
                "initial_value": str(phone)[:150]
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "email_block",
            "label": {"type": "plain_text", "text": "Email"},
            "element": {
                "type": "plain_text_input",
                "action_id": "email",
                "initial_value": str(email)[:150]
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "planning_area_block",
            "label": {"type": "plain_text", "text": "Planning Area"},
            "element": {
                "type": "plain_text_input",
                "action_id": "planning_area",
                "initial_value": str(planning_area)[:150]
            },
            "optional": True
        },

        # Categorization Section
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Categorization"}
        },
    ])

    # Build multi-select elements (values are comma-separated strings)
    who_is_it_for_element = {
        "type": "multi_static_select",
        "action_id": "who_is_it_for",
        "placeholder": {"type": "plain_text", "text": "Select target audiences"},
        "options": who_is_it_for_options,
    }
    initial_who = get_initial_options(who_is_it_for or "", who_is_it_for_options)
    if initial_who:
        who_is_it_for_element["initial_options"] = initial_who

    what_it_gives_element = {
        "type": "multi_static_select",
        "action_id": "what_it_gives",
        "placeholder": {"type": "plain_text", "text": "Select benefit types"},
        "options": what_it_gives_options,
    }
    initial_what = get_initial_options(what_it_gives or "", what_it_gives_options)
    if initial_what:
        what_it_gives_element["initial_options"] = initial_what

    scheme_type_element = {
        "type": "multi_static_select",
        "action_id": "scheme_type",
        "placeholder": {"type": "plain_text", "text": "Select scheme categories"},
        "options": scheme_type_options,
    }
    initial_type = get_initial_options(scheme_type or "", scheme_type_options)
    if initial_type:
        scheme_type_element["initial_options"] = initial_type

    blocks.extend([
        {
            "type": "input",
            "block_id": "who_is_it_for_block",
            "label": {"type": "plain_text", "text": "Who is it for?"},
            "element": who_is_it_for_element,
            "optional": True
        },
        {
            "type": "input",
            "block_id": "what_it_gives_block",
            "label": {"type": "plain_text", "text": "What it gives"},
            "element": what_it_gives_element,
            "optional": True
        },
        {
            "type": "input",
            "block_id": "scheme_type_block",
            "label": {"type": "plain_text", "text": "Scheme Type"},
            "element": scheme_type_element,
            "optional": True
        },

        # Description Section
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Scheme Details"}
        },
        {
            "type": "input",
            "block_id": "llm_description_block",
            "label": {"type": "plain_text", "text": "Description"},
            "element": {
                "type": "plain_text_input",
                "action_id": "llm_description",
                "multiline": True,
                "initial_value": str(llm_description)[:2900]
            }
        },
        {
            "type": "input",
            "block_id": "eligibility_block",
            "label": {"type": "plain_text", "text": "Eligibility"},
            "element": {
                "type": "plain_text_input",
                "action_id": "eligibility",
                "multiline": True,
                "initial_value": str(eligibility)[:2900]
            },
            "optional": True
        },
        {
            "type": "input",
            "block_id": "how_to_apply_block",
            "label": {"type": "plain_text", "text": "How to Apply"},
            "element": {
                "type": "plain_text_input",
                "action_id": "how_to_apply",
                "multiline": True,
                "initial_value": str(how_to_apply)[:2900]
            },
            "optional": True
        }
    ])

    return {
        "type": "modal",
        "callback_id": "new_scheme_approval_submit",
        "title": {"type": "plain_text", "text": "Approve New Scheme"},
        "submit": {"type": "plain_text", "text": "Approve & Add"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": metadata,
        "blocks": blocks
    }


def build_new_scheme_approved_message(
    doc_id: str,
    scheme_name: str,
    scheme_url: str,
    reviewer_id: str,
    reviewed_at: str,
    new_scheme_id: str
) -> dict:
    """
    Build message confirming scheme was approved and added.

    Args:
        doc_id: Original schemeEntries document ID
        scheme_name: Approved scheme name
        scheme_url: Scheme URL
        reviewer_id: Slack user ID of reviewer
        reviewed_at: ISO timestamp of approval
        new_scheme_id: New document ID in schemes collection

    Returns:
        Slack message payload
    """
    reviewed_by = f"<@{reviewer_id}>" if reviewer_id else "a reviewer"

    return {
        "text": f"New scheme '{scheme_name}' has been approved and added.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: *New scheme approved and added!*\n\n*{scheme_name}*\n<{scheme_url}|View Scheme>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Approved by {reviewed_by}"},
                    {"type": "mrkdwn", "text": f"At: {reviewed_at}"},
                    {"type": "mrkdwn", "text": f"Scheme ID: `{new_scheme_id}`"},
                    {"type": "mrkdwn", "text": f"Entry ID: `{doc_id}`"}
                ]
            }
        ]
    }


def build_new_scheme_rejected_message(
    doc_id: str,
    scheme_name: str,
    reviewer_id: str,
    reason: Optional[str] = None
) -> dict:
    """
    Build message confirming scheme was rejected.

    Args:
        doc_id: schemeEntries document ID
        scheme_name: Rejected scheme name
        reviewer_id: Slack user ID of reviewer
        reason: Optional rejection reason

    Returns:
        Slack message payload
    """
    reviewed_by = f"<@{reviewer_id}>" if reviewer_id else "a reviewer"
    reason_text = f"\nReason: {reason}" if reason else ""

    return {
        "text": f"Scheme submission '{scheme_name}' was rejected.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":x: *Scheme submission rejected*\n\n*{scheme_name}*{reason_text}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Rejected by {reviewed_by}"},
                    {"type": "mrkdwn", "text": f"Entry ID: `{doc_id}`"}
                ]
            }
        ]
    }


def build_new_scheme_duplicate_message(
    doc_id: str,
    submission_data: Dict[str, Any],
    duplicate_info: Dict[str, Any]
) -> dict:
    """
    Build Slack message for scheme that already exists.

    Args:
        doc_id: schemeEntries document ID
        submission_data: Original submission data
        duplicate_info: Info about existing duplicate scheme

    Returns:
        Slack message payload
    """
    scheme_name = submission_data.get("Scheme", "Unknown")
    scheme_url = submission_data.get("Link", "")
    domain = duplicate_info.get("domain", "")
    existing_scheme_name = duplicate_info.get("scheme", "")
    existing_url = duplicate_info.get("link", "")

    return {
        "text": f"Scheme already exists: {scheme_name}",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Scheme Already Exists", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":no_entry: *This scheme was not added because it already exists in the database.*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Submitted URL:*\n<{scheme_url}|{scheme_url}>"},
                    {"type": "mrkdwn", "text": f"*Domain:*\n`{domain}`"}
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Existing scheme in database:*\n"
                           f"• *Name:* {existing_scheme_name}\n"
                           f"• *URL:* <{existing_url}|{existing_url}>\n"
                           f"• *ID:* `{duplicate_info['doc_id']}`"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Entry ID: `{doc_id}` | Submitted by: anonymous user"}
                ]
            }
        ]
    }
