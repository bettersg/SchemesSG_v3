import logging
import os

import requests
from dotenv import load_dotenv

from utils.auth import get_id_token
from utils.format import format_text


load_dotenv()
backend_url = os.getenv("BACKEND_URL")


def search_schemes(text: str, similarity_threshold: int) -> tuple[str | None, list | None, str | None]:
    """
    Handles API call to backend (searching for schemes)

    Args:
        text (str): user query for schemes search
        similarity_threshold (int): similarity threshold

    Returns:
        str | None: ID of query
        list | None: list of most relevant schemes
        str | None: error message to be displayed if error occurs
    """

    id_token = get_id_token()

    if id_token is None:
        err_message = "Authentication failed!"
        return (None, None, err_message)

    body = {"query": text, "similarity_threshold": similarity_threshold}

    endpoint = backend_url + "/schemes_search"

    res = requests.post(
        endpoint,
        json=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"},
    )

    if res.status_code != 200:  # Error
        logging.error(f"Request failed! (schemes_search)\tMessage: {res.json()['error']}")
        err_message = "I am unable to search for suitable assistance schemes. Please try again!"
        return (None, None, err_message)

    schemes = res.json()["data"]
    query_id = res.json()["sessionID"]

    if not schemes:  # No suitable schemes found
        err_message = "Sorry, I am unable to find a suitable assistance scheme to address your needs."
        return (query_id, None, err_message)

    return (query_id, schemes, None)


def retrieve_scheme_results(query_id: str) -> bool | list[dict[str, str | int]]:
    """
    Handles API call to retrieve full search results of a query

    Args:
        query_id (str): ID of search query; to be used to retrieve full schemes result from firestore

    Returns:
        bool | list[dict[str, str | int]]: either returns False (in which case provided query_id is in incorrect) or full schemes result
    """

    id_token = get_id_token()

    if id_token is None:
        return False

    endpoint = backend_url + "/retrieve_search_queries" + "/" + query_id

    res = requests.get(
        endpoint,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"},
    )

    if res.status_code != 200: # Error
        logging.error(f"Request failed! (retrieve_search_queries)\tMessage: {res.json()['error']}")
        return False

    return res.json()["data"]["schemes_response"]


def send_chat_message(input_text: str, query_id: str) -> tuple[str | None, str | None]:
    """
    Handles API call to backend (chat bot)

    Args:
        input_text (str): message by user to be sent to chat bot
        query_id (str): ID of search query; to be sent to backend so chat bot can use the search results as a context

    Returns:
        str | None: response message by chat bot
        str | None: error message should chat bot not work
    """

    id_token = get_id_token()

    if id_token is None:
        err_message = "Authentication failed!"
        return (None, err_message)

    chatbot_query = input_text + "\n\nKeep the response to a strict maximum of 300 words."
    body = {"sessionID": query_id, "message": chatbot_query}

    endpoint = backend_url + "/chat_message"

    res = requests.post(
        endpoint,
        json=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"},
    )

    if res.status_code != 200:  # Error
        logging.error(f"Request failed! (chat_message)\tMessage: {res.json()['error']}")
        err_message = "Sorry, Schemes Support Chat is unable to work currently."
        return (None, err_message)

    message = format_text(res.json()["message"])

    return (message, None)
