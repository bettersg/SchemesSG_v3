"""Prompts for follow-up suggestion generation."""

FOLLOWUP_SYSTEM_TEMPLATE = """Return exactly one valid JSON object containing up to {max_pairs} key-value pairs. Do not include markdown, explanations, headings, or extra text.

Each key must be a short action label with a maximum of 3 words. Each value must be a single concise action request written from the user's perspective, starting with a verb such as 'Find', 'Compare', 'Filter', 'Check', or 'Explore'.

Do not ask the user to provide information directly using phrases like 'Provide', 'Share', 'Enter', or 'Indicate'. Instead, rewrite the request as a user goal that depends on required information. When user input is required, describe the needed information plainly within the action phrase. Placeholders must describe the needed information from the user's perspective, such as 'my country', 'my education level', 'my income', or 'my interests'.

Bad example: 'Provide my country, education level, and field of interest'. Good example: 'Find scholarships based on my country, my education level, and my field of interest'. Bad example: 'Indicate my education level to find relevant scholarships'. Good example: 'Find relevant scholarships based on my education level'.

Every value must represent a final user intent or outcome, not a data collection step.

Language: determine the language from the user's own messages (the 'human' turns) only — ignore the language of scheme names, agency names, and other data, which may appear in Chinese, Malay, or Tamil regardless of how the user writes. Write the labels and values in that language on a best-effort basis (Chinese only if the user writes in Chinese, Malay if Malay, and so on). Default to English whenever the user's language is mixed, unclear, or English. The verbs listed above (Find, Compare, Filter, Check, Explore) describe the kind of action expected — express that action naturally in the user's language rather than copying the English word. Keep proper nouns (scheme names, agency names, URLs) in their original form. The JSON structure, key/value rules, and 3-word label limit still apply regardless of language."""

FOLLOWUP_PROMPT_TEMPLATE = """Generate suggested follow-up actions for this conversation.
Schemes found:
{schemes_json}
Conversation:
{transcript}
Format example: {{"Filter schemes": "Filter schemes by eligibility criteria", "Get contacts": "Retrieve contact details for shortlisted programs"}}"""

DEFAULT_FOLLOWUP_KV = {
    "Filter schemes": "Filter schemes by eligibility criteria",
    "Compare options": "Compare top schemes by benefits and fit",
    "Get contacts": "Retrieve contact details for shortlisted programs",
}
