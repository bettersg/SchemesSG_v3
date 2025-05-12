import re
from typing import Match

from aiogram import html


def replace_with_html_italics(match: Match[str]) -> str:
    """
    Adds HTML italic tags to matching text

    Args:
        match (Match[str]): matching text

    Returns:
        str: italicised text
    """

    text = match.group(1)
    return html.italic(text)


def replace_with_html_bold(match: Match[str]) -> str:
    """
    Adds HTML bold tags to matching text

    Args:
        match (Match[str]): matching text

    Returns:
        str: bolded text
    """

    text = match.group(1)
    return html.bold(text)


def format_text(text: str) -> str:
    """
    Formats LLM-generated text for telegram

    Args:
        text (str): unformatted text from chat_message firebase function

    Returns:
        str: formatted text to be displayed as a telegram message
    """

    text = re.sub(r'\*\*(.+?)\*\*', replace_with_html_bold, text or "")

    text = re.sub(r'### (.+)', replace_with_html_italics, text or "")

    return text
