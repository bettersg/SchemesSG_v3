"""
This is the main file for the Firebase Functions.

Import the functions you want to use here.
Search and chat services will be added soon.

To run the functions locally, run `firebase emulators:start`.
Do not deploy the functions using firebase deploy, deployment will be handled automatically via Github Actions.
"""

import json

from dummy.bar import bar  # noqa: F401
from dummy.foo import foo  # noqa: F401
from firebase_admin import initialize_app
from firebase_functions import https_fn
from search.search import schemespredict  # noqa: F401


# Initialize the Firebase Admin SDK
initialize_app()


# Dummy endpoint
@https_fn.on_request(region="asia-southeast1")
def main(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello from Firebase!")


@https_fn.on_request(region="asia-southeast1")
def health(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response(
        response = json.dumps({"status": "ok"}),
        status = 200,
        mimetype = "application/json"
    )
