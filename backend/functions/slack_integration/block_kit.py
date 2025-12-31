"""
Build a Slack message with a Review button for a given row in the scraping errors table.
"""


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

    Dropdowns:
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
    who_is_it_for = data.get("who_is_it_for", "")
    what_it_gives = data.get("what_it_gives", "")
    scheme_type = data.get("scheme_type", "")
    llm_description = data.get("llm_description", "")
    eligibility = data.get("eligibility", "")
    how_to_apply = data.get("how_to_apply", "")

    # Dropdown options (can be customized based on your needs)
    who_is_it_for_options = [
        {"text": {"type": "plain_text", "text": "Individuals"}, "value": "individuals"},
        {"text": {"type": "plain_text", "text": "Families"}, "value": "families"},
        {"text": {"type": "plain_text", "text": "Seniors"}, "value": "seniors"},
        {"text": {"type": "plain_text", "text": "Youth"}, "value": "youth"},
        {"text": {"type": "plain_text", "text": "Persons with Disabilities"}, "value": "pwd"},
        {"text": {"type": "plain_text", "text": "Low Income"}, "value": "low_income"},
        {"text": {"type": "plain_text", "text": "Businesses"}, "value": "businesses"},
    ]

    what_it_gives_options = [
        {"text": {"type": "plain_text", "text": "Financial Assistance"}, "value": "financial_assistance"},
        {"text": {"type": "plain_text", "text": "Subsidies"}, "value": "subsidies"},
        {"text": {"type": "plain_text", "text": "Grants"}, "value": "grants"},
        {"text": {"type": "plain_text", "text": "Loans"}, "value": "loans"},
        {"text": {"type": "plain_text", "text": "Education Support"}, "value": "education_support"},
        {"text": {"type": "plain_text", "text": "Healthcare Support"}, "value": "healthcare_support"},
        {"text": {"type": "plain_text", "text": "Housing Support"}, "value": "housing_support"},
        {"text": {"type": "plain_text", "text": "Training/Employment"}, "value": "training_employment"},
    ]

    scheme_type_options = [
        {"text": {"type": "plain_text", "text": "Financial Aid"}, "value": "financial_aid"},
        {"text": {"type": "plain_text", "text": "Education"}, "value": "education"},
        {"text": {"type": "plain_text", "text": "Healthcare"}, "value": "healthcare"},
        {"text": {"type": "plain_text", "text": "Housing"}, "value": "housing"},
        {"text": {"type": "plain_text", "text": "Employment"}, "value": "employment"},
        {"text": {"type": "plain_text", "text": "Social Services"}, "value": "social_services"},
        {"text": {"type": "plain_text", "text": "Business Support"}, "value": "business_support"},
    ]

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

    # Build dropdown elements conditionally (only add initial_option if value exists)
    who_is_it_for_element = {
        "type": "static_select",
        "action_id": "who_is_it_for",
        "placeholder": {"type": "plain_text", "text": "Select target audience"},
        "options": who_is_it_for_options,
    }
    if who_is_it_for:
        initial = next((opt for opt in who_is_it_for_options if opt["value"] == who_is_it_for), None)
        if initial:
            who_is_it_for_element["initial_option"] = initial

    what_it_gives_element = {
        "type": "static_select",
        "action_id": "what_it_gives",
        "placeholder": {"type": "plain_text", "text": "Select benefit type"},
        "options": what_it_gives_options,
    }
    if what_it_gives:
        initial = next((opt for opt in what_it_gives_options if opt["value"] == what_it_gives), None)
        if initial:
            what_it_gives_element["initial_option"] = initial

    scheme_type_element = {
        "type": "static_select",
        "action_id": "scheme_type",
        "placeholder": {"type": "plain_text", "text": "Select scheme category"},
        "options": scheme_type_options,
    }
    if scheme_type:
        initial = next((opt for opt in scheme_type_options if opt["value"] == scheme_type), None)
        if initial:
            scheme_type_element["initial_option"] = initial

    blocks.extend(
        [
            {
                "type": "input",
                "block_id": "who_is_it_for_block",
                "label": {"type": "plain_text", "text": "Who is it for?"},
                "element": who_is_it_for_element,
            },
            {
                "type": "input",
                "block_id": "what_it_gives_block",
                "label": {"type": "plain_text", "text": "What it gives"},
                "element": what_it_gives_element,
            },
            {
                "type": "input",
                "block_id": "scheme_type_block",
                "label": {"type": "plain_text", "text": "Scheme Type"},
                "element": scheme_type_element,
            },
            # Text Areas Section
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
