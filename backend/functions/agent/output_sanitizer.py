"""Sanitizers for assistant-generated text."""

import unicodedata


SCRIPT_KEYWORDS = {
    "TAMIL": "Tamil",
}


def _script_for_char(char: str) -> str | None:
    try:
        name = unicodedata.name(char)
    except ValueError:
        return None

    for keyword, script in SCRIPT_KEYWORDS.items():
        if keyword in name:
            return script
    return None


def scripts_present(text: str) -> set[str]:
    return {script for char in text for script in [_script_for_char(char)] if script is not None}


def sanitize_assistant_text_for_user_scripts(text: str, user_text: str) -> str:
    """Remove generated script characters that were absent from user input.

    Scheme data can contain multilingual names, so this is intentionally applied
    only to final assistant prose, not tool payloads or retrieved scheme records.
    """

    allowed_scripts = scripts_present(user_text)
    if not allowed_scripts and not any(_script_for_char(char) for char in text):
        return text

    sanitized_chars: list[str] = []
    for char in text:
        script = _script_for_char(char)
        if script is None or script in allowed_scripts:
            sanitized_chars.append(char)
    return "".join(sanitized_chars)
