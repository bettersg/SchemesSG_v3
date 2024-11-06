"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes
"""

import json

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn
from loguru import logger


firebase_manager = FirebaseManager()


@https_fn.on_request(region="asia-southeast1")
def schemes(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for single schemes page endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    global firebase_manager

    if not req.method == "GET":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only GET is supported"}),
            status=405,
            mimetype="application/json",
        )

    splitted_path = req.path.split("/")
    schemes_id = splitted_path[1] if len(splitted_path) == 2 else None

    if not schemes_id:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid path parameters, please provide schemes id"}),
            status=400,
            mimetype="application/json",
        )

    try:
        ref = firebase_manager.firestore_client.collection("schemes").document(schemes_id)
        doc = ref.get()
    except Exception as e:
        logger.exception("Unable to fetch scheme from firestore", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error, unable to fetch scheme from firestore"}),
            status=500,
            mimetype="application/json",
        )

    if not doc.exists:
        return https_fn.Response(
            response=json.dumps({"error": "Scheme with provided id does not exist"}),
            status=404,
            mimetype="application/json",
        )

    results = {"data": doc.to_dict(), "mh": 0.7}
    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json")
