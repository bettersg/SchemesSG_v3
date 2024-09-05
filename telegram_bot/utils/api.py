import os
import uuid

import requests
from dotenv import load_dotenv


load_dotenv()
backend_url = os.getenv("BACKEND_URL")


def search_schemes(text: str, similarity_threshold: int) -> tuple[str, list | None, str | None]:
    """
    Handles API Call to backend
    """

    query_id = str(uuid.uuid4())
    body = {"sessionID": query_id, "query": text, "similarity_threshold": similarity_threshold}

    endpoint = backend_url + "/schemespredict"

    res = requests.post(endpoint, json=body)

    if res.status_code != 200: # Error
        err_message = "I am unable to search for suitable assistance schemes. Please try again!"
        return (query_id, None, err_message)

    schemes = res.json()["data"]

    if len(schemes) == 0:  # No suitable schemes found
        err_message = "Sorry, I am unable to find a suitable assistance scheme to address your needs."
        return (query_id, None, err_message)

    return (query_id, schemes, None)
