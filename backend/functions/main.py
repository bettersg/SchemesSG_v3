"""
This is the main file for the Firebase Functions.

Import the functions you want to use here.
Search and chat services will be added soon.

To run the functions locally, run `firebase emulators:start`.
Do not deploy the functions using firebase deploy, deployment will be handled automatically via Github Actions.
"""

import json
import sys

from chat.chat import chat_message  # noqa: F401
from fb_manager.firebaseManager import FirebaseManager
from feedback.feedback import feedback  # noqa: F401
from firebase_functions import https_fn, options
from loguru import logger
from schemes.schemes import schemes  # noqa: F401
from schemes.search import schemes_search  # noqa: F401
from update_scheme.update_scheme import update_scheme  # noqa: F401


# Initialise logger
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    colorize=True,
    backtrace=True,
)
logger.info("Logger initialised")

# Initialise the Firebase Admin SDK and Connection to firestore
firebase_manager = FirebaseManager()


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Increases memory to 1GB
)
def health(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for health check endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    return https_fn.Response(response=json.dumps({"status": "ok"}), status=200, mimetype="application/json")
