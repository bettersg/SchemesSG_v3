"""
Build a Slack message with a Review button for a given row in the scraping errors table.
"""

from new_scheme.constants import SCHEME_TYPE, WHAT_IT_GIVES, WHO_IS_IT_FOR


def build_review_message(doc_id: str, data: dict) -> dict:
    scheme_name = data.get("scheme_name", "(no name)")
    scheme_url = data.get("scheme_url", "")
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*New scraping issue* for *{scheme_name}*\n<{scheme_url}|Open link>",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Review"},
                        "action_id": "review_scheme",
                        "value": doc_id,
                    }
                ],
            },
        ]
    }


def build_review_modal(metadata: str, data: dict) -> dict:
    """
    Build review modal form matching the architecture diagram.

    Pre-filled Text Fields:
    - Scheme Name
    - Agency
    - Image URL
    - Phone
    - Address

    Multi-select dropdowns (aligned with new_scheme constants):
    - who_is_it_for
    - what_it_gives
    - scheme_type

    Text Areas:
    - llm_description
    - eligibility
    - how_to_apply
    """
    scheme_name = data.get("scheme_name", "")
    agency = data.get("agency", "")
    image_url = data.get("image_url", "")
    phone = data.get("phone", "")
    address = data.get("address", "")
    who_is_it_for = data.get("who_is_it_for", [])
    what_it_gives = data.get("what_it_gives", [])
    scheme_type = data.get("scheme_type", [])
    llm_description = data.get("llm_description", "")
    eligibility = data.get("eligibility", "")
    how_to_apply = data.get("how_to_apply", "")

    # Normalise to list (handle legacy CSV strings in existing data)
    def to_list(value) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            return [v.strip() for v in value.split(",") if v.strip()]
        return []

    who_is_it_for = to_list(who_is_it_for)
    what_it_gives = to_list(what_it_gives)
    scheme_type = to_list(scheme_type)

    # Build options from shared constants (same lists used by new_scheme pipeline)
    who_is_it_for_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]} for opt in WHO_IS_IT_FOR
    ]
    what_it_gives_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]} for opt in WHAT_IT_GIVES
    ]
    scheme_type_options = [
        {"text": {"type": "plain_text", "text": opt[:75]}, "value": opt[:75]} for opt in SCHEME_TYPE
    ]

    def get_initial_options(values: list, options: list) -> list:
        """Return matching option dicts for the given values list."""
        value_set = set(values)
        return [opt for opt in options if opt["value"] in value_set][:10]

    blocks = [
        # Pre-filled Text Fields Section
        {"type": "header", "text": {"type": "plain_text", "text": "Basic Information"}},
        {
            "type": "input",
            "block_id": "scheme_name_block",
            "label": {"type": "plain_text", "text": "Scheme Name"},
            "element": {"type": "plain_text_input", "action_id": "scheme_name", "initial_value": scheme_name},
        },
        {
            "type": "input",
            "block_id": "agency_block",
            "label": {"type": "plain_text", "text": "Agency"},
            "element": {"type": "plain_text_input", "action_id": "agency", "initial_value": agency},
        },
        {
            "type": "input",
            "block_id": "image_url_block",
            "label": {"type": "plain_text", "text": "Image URL"},
            "element": {"type": "plain_text_input", "action_id": "image_url", "initial_value": image_url},
            "optional": True,
        },
        {
            "type": "input",
            "block_id": "phone_block",
            "label": {"type": "plain_text", "text": "Phone"},
            "element": {"type": "plain_text_input", "action_id": "phone", "initial_value": phone},
            "optional": True,
        },
        {
            "type": "input",
            "block_id": "address_block",
            "label": {"type": "plain_text", "text": "Address"},
            "element": {
                "type": "plain_text_input",
                "action_id": "address",
                "initial_value": address,
                "multiline": True,
            },
            "optional": True,
        },
        # Dropdowns Section
        {"type": "header", "text": {"type": "plain_text", "text": "Categorization"}},
    ]

    # Build multi-select elements
    who_is_it_for_element = {
        "type": "multi_static_select",
        "action_id": "who_is_it_for",
        "placeholder": {"type": "plain_text", "text": "Select target audiences"},
        "options": who_is_it_for_options,
    }
    initial_who = get_initial_options(who_is_it_for, who_is_it_for_options)
    if initial_who:
        who_is_it_for_element["initial_options"] = initial_who

    what_it_gives_element = {
        "type": "multi_static_select",
        "action_id": "what_it_gives",
        "placeholder": {"type": "plain_text", "text": "Select benefit types"},
        "options": what_it_gives_options,
    }
    initial_what = get_initial_options(what_it_gives, what_it_gives_options)
    if initial_what:
        what_it_gives_element["initial_options"] = initial_what

    scheme_type_element = {
        "type": "multi_static_select",
        "action_id": "scheme_type",
        "placeholder": {"type": "plain_text", "text": "Select scheme categories"},
        "options": scheme_type_options,
    }
    initial_type = get_initial_options(scheme_type, scheme_type_options)
    if initial_type:
        scheme_type_element["initial_options"] = initial_type

    blocks.extend(
        [
            {
                "type": "input",
                "block_id": "who_is_it_for_block",
                "label": {"type": "plain_text", "text": "Who is it for?"},
                "element": who_is_it_for_element,
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "what_it_gives_block",
                "label": {"type": "plain_text", "text": "What it gives"},
                "element": what_it_gives_element,
                "optional": True,
            },
            {
                "type": "input",
                "block_id": "scheme_type_block",
                "label": {"type": "plain_text", "text": "Scheme Type"},
                "element": scheme_type_element,
                "optional": True,
            },
            # Text Areas Section
            {"type": "header", "text": {"type": "plain_text", "text": "LLM Extracted Fields"}},
            {
                "type": "input",
                "block_id": "llm_description_block",
                "label": {"type": "plain_text", "text": "Description"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "llm_description",
                    "multiline": True,
                    "initial_value": llm_description[:2900],
                },
            },
            {
                "type": "input",
                "block_id": "eligibility_block",
                "label": {"type": "plain_text", "text": "Eligibility"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "eligibility",
                    "multiline": True,
                    "initial_value": eligibility[:2900],
                },
            },
            {
                "type": "input",
                "block_id": "how_to_apply_block",
                "label": {"type": "plain_text", "text": "How to Apply"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "how_to_apply",
                    "multiline": True,
                    "initial_value": how_to_apply[:2900],
                },
            },
        ]
    )

    return {
        "type": "modal",
        "callback_id": "review_submit",
        "title": {"type": "plain_text", "text": "Review Scheme"},
        "submit": {"type": "plain_text", "text": "Approve & Save"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": metadata,
        "blocks": blocks,
    }


def build_review_locked_message(doc_id: str, data: dict, user_id: str, reviewed_at: str) -> dict:
    scheme_name = data.get("scheme_name", "(no name)")
    scheme_url = data.get("scheme_url", "")
    scraped_text = data.get("scraped_text", "")
    reviewed_by = f"<@{user_id}>" if user_id else "a reviewer"
    reviewed_text = f"Reviewed by {reviewed_by} on {reviewed_at}"
    return {
        "text": f"Review for {scheme_name} is complete.",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Scraping issue resolved* for *{scheme_name}*\n<{scheme_url}|Open link>",
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": f"> {scraped_text[:2900]}"}},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": reviewed_text},
                    {"type": "mrkdwn", "text": f"Record ID: `{doc_id}`"},
                ],
            },
        ],
    }
