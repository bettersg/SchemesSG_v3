"""Prompt constants for follow-up suggestion generation."""

MAX_FOLLOWUP_KV = 5

FOLLOWUP_SYSTEM_TEMPLATE = (
    "Return exactly JSON object with up to {max_pairs} key-value pairs. "
    "Each key must be a short label with at most 3 words. "
    "Each value must be a concise user-intent action phrase written in first-person user voice. "
    "Use first-person pronouns such as 'my', 'me', or 'I'. "
    "When asking for personal profile details, use first-person fill-in sentence templates "
    "such as 'I am [age] and I am [employment status].' "
    "Do NOT phrase these as 'Share my ...' or 'Provide my ...'. "
    "Do NOT use third-person references like 'user', 'the user', or \"user's\". "
    "Do NOT use assistant-perspective phrasing such as 'Would you like...' or 'Can I help...'. "
    "For non-profile actions, use concise first-person request/action phrasing. "
    "No markdown, no code fences, no extra keys."
)

FOLLOWUP_PROMPT_TEMPLATE = (
    "Generate suggested follow-up actions for this conversation.\n"
    "Conversation:\n{transcript}\n"
    'Format example: {{"Profile details": "I am [age] and I am [employment status].", '
    '"Get contacts": "Retrieve contact details for shortlisted programs"}}'
)

DEFAULT_FOLLOWUP_KV = {
    "Filter schemes": "Filter schemes by eligibility criteria",
    "Compare options": "Compare top schemes by benefits and fit",
    "Get contacts": "Retrieve contact details for shortlisted programs",
    "Explore more": "Show more schemes related to my query",
    "Check deadlines": "Check deadlines and application steps for shortlisted schemes",
}
