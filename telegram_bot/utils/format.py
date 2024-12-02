import re


def format_chat_text(text: str) -> str:
    """
    Formats text from chatbot for telegram

    Args:
        text (str): unformatted text from chat_message firebase function

    Returns:
        str: formatted text to be displayed as a telegram message
    """

    # Replace ** with *
    text = re.sub(r'\*\*', '*', text)

    # Replace ### Header with _Header_ (italic effect)
    text = re.sub(r'### (.+)', r'_\1_', text)

    return text
