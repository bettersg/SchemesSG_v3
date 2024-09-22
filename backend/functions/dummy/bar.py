"""
This is a dummy file for testing.

url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/us-central1/bar
"""

from firebase_functions import https_fn


@https_fn.on_request()
def bar(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response("Hello foo!")
