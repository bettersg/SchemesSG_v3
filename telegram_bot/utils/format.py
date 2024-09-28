import re


def format_chat_text(text: str) -> str:
    """
    Formats text from chatbot for telegram
    """

    # Replace ** with *
    text = re.sub(r'\*\*', '*', text)

    # Replace ### Header with _Header_ (italic effect)
    text = re.sub(r'### (.+)', r'_\1_', text)

    return text
