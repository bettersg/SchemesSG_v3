"""Prompts for follow-up suggestion generation."""

FOLLOWUP_SYSTEM_TEMPLATE = (
    "Return exactly one valid JSON object containing up to {max_pairs} key-value pairs. "
    "Do not include markdown, explanations, headings, or extra text. "
    "Each key must be a short action label with a maximum of 3 words. "
    "Each value must be a single concise action request written from the user's perspective, starting with a verb such as 'Find', 'Compare', 'Filter', 'Check', or 'Explore'. "
    "Do not ask the user to provide information directly using phrases like 'Provide', 'Share', 'Enter', or 'Indicate'. "
    "Instead, rewrite the request as a user goal that depends on required information. "
    "When user input is required, include placeholders in square brackets within the action phrase. "
    "Placeholders must describe the needed information from the user's perspective, such as '[my country]', '[my education level]', '[my income]', or '[my interests]'. "
    "Bad example: 'Provide my country, education level, and field of interest'. "
    "Good example: 'Find scholarships based on [my country], [my education level], and [my field of interest]'. "
    "Bad example: 'Indicate my education level to find relevant scholarships'. "
    "Good example: 'Find relevant scholarships based on [my education level]'. "
    "Every value must represent a final user intent or outcome, not a data collection step."
)

FOLLOWUP_PROMPT_TEMPLATE = (
    "Generate suggested follow-up actions for this conversation.\n"
    "Schemes found:\n{schemes_json}\n"
    "Conversation:\n{transcript}\n"
    'Format example: {{"Filter schemes": "Filter schemes by eligibility criteria", '
    '"Get contacts": "Retrieve contact details for shortlisted programs"}}'
)

DEFAULT_FOLLOWUP_KV = {
    "Filter schemes": "Filter schemes by eligibility criteria",
    "Compare options": "Compare top schemes by benefits and fit",
    "Get contacts": "Retrieve contact details for shortlisted programs",
}
