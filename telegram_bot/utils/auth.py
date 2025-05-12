import logging
import os

import firebase_admin
import requests
from dotenv import load_dotenv
from firebase_admin import auth, credentials


load_dotenv()
creds = credentials.Certificate(os.getenv("FB_CREDS_PATH"))

firebase_admin.initialize_app(creds)


def get_id_token() -> str | None:
    """
    Function to make warm-up request for authentication token

    Returns:
        - str | None: authentication token
    """

    custom_token = auth.create_custom_token("warmup-user")

    response = requests.post(
        "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken",
        params={"key": os.getenv("FB_API_KEY")},
        json={"token": custom_token.decode(), "returnSecureToken": True},
    )

    if response.status_code != 200:
        res_json = response.json()
        logging.error(f"Authetication Failed!\tCode: {res_json['error']['code']}\tMessage: {res_json['error']['message']}")
        return None

    id_token = response.json()["idToken"]

    return id_token
