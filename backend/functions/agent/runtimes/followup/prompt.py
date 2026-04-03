"""Prompt constants for follow-up suggestion generation."""

MAX_FOLLOWUP_KV = 5

FOLLOWUP_SYSTEM_TEMPLATE = (
    "Return exactly JSON object with up to {max_pairs} key-value pairs. "
    "Each key must be a short label with at most 3 words. "
    "Each value must be a concise user-intent action phrase, written from the user's perspective. "
    "Do NOT use assistant-perspective phrasing such as 'Would you like...' or 'Can I help...'. "
    "Use imperative/request style such as 'Retrieve contact details for ...' or 'Compare top schemes by ...'. "
    "No markdown, no code fences, no extra keys."
)

FOLLOWUP_PROMPT_TEMPLATE = (
    "Generate suggested follow-up actions for this conversation.\n"
    "Conversation:\n{transcript}\n"
    'Format example: {{"Filter schemes": "Filter schemes by eligibility criteria", '
    '"Get contacts": "Retrieve contact details for shortlisted programs"}}'
)

DEFAULT_FOLLOWUP_KV = {
    "Filter schemes": "Filter schemes by eligibility criteria",
    "Compare options": "Compare top schemes by benefits and fit",
    "Get contacts": "Retrieve contact details for shortlisted programs",
    "Explore more": "Show more schemes related to my query",
    "Check deadlines": "Check deadlines and application steps for shortlisted schemes",
}
