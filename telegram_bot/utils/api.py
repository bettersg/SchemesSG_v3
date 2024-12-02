import os

import requests
from dotenv import load_dotenv

from utils.format import format_chat_text


load_dotenv()
backend_url = os.getenv("BACKEND_URL")


def search_schemes(text: str, similarity_threshold: int) -> tuple[str | None, list | None, str | None]:
    """
    Handles API call to backend (searching for schemes)
    """

    body = {"query": text, "similarity_threshold": similarity_threshold}

    endpoint = backend_url + "/schemes_search"

    res = requests.post(endpoint, json=body)

    if res.status_code != 200:  # Error
        err_message = "I am unable to search for suitable assistance schemes. Please try again!"
        return (None, None, err_message)

    schemes = res.json()["data"]
    query_id = res.json()["sessionID"]

    if not schemes:  # No suitable schemes found
        err_message = "Sorry, I am unable to find a suitable assistance scheme to address your needs."
        return (query_id, None, err_message)

    return (query_id, schemes, None)


def send_chat_message(input_text: str, query_id: str) -> tuple[str | None, str | None]:
    """
    Handles API call to backend (chat bot)
    """

    chatbot_query = input_text + "\n\nKeep the response to 4096 characters"
    body = {"sessionID": query_id, "message": chatbot_query}

    endpoint = backend_url + "/chat_message"

    res = requests.post(endpoint, json=body)

    if res.status_code != 200:  # Error
        err_message = "Sorry, Schemes Support Chat is unable to work currently."
        return (None, err_message)

    message = format_chat_text(res.json()["message"])

    return (message, None)
