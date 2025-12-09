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
                    "text": f"*New scraping issue* for *{scheme_name}*\n<{scheme_url}|Open link>"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Review"},
                        "action_id": "review_scheme",
                        "value": doc_id
                    }
                ]
            }
        ]
    }


def build_review_modal(metadata: str, data: dict) -> dict:
    scheme_name = data.get("scheme_name", "")
    scheme_url = data.get("scheme_url", "")
    scraped_text = data.get("scraped_text", "")
    return {
        "type": "modal",
        "callback_id": "review_submit",
        "title": {"type": "plain_text", "text": "Review scraping error"},
        "submit": {"type": "plain_text", "text": "Approve & Save"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": metadata,
        "blocks": [
            {
                "type": "input",
                "block_id": "scheme_name_block",
                "label": {"type": "plain_text", "text": "Scheme name"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "scheme_name",
                    "initial_value": scheme_name
                }
            },
            {
                "type": "input",
                "block_id": "scheme_url_block",
                "label": {"type": "plain_text", "text": "Scheme URL"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "scheme_url",
                    "initial_value": scheme_url
                }
            },
            {
                "type": "input",
                "block_id": "scraped_text_block",
                "label": {"type": "plain_text", "text": "Scraped text"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "scraped_text",
                    "multiline": True,
                    "initial_value": scraped_text[:2900]
                }
            }
        ]
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
                    "text": f"*Scraping issue resolved* for *{scheme_name}*\n<{scheme_url}|Open link>"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"> {scraped_text[:2900]}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": reviewed_text},
                    {"type": "mrkdwn", "text": f"Record ID: `{doc_id}`"}
                ]
            }
        ]
    }

