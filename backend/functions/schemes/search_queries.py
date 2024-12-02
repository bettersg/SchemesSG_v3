"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search
"""

import json

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger


def create_firebase_manager() -> FirebaseManager:
    """Factory function to create a FirebaseManager instance."""

    return FirebaseManager()


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Increases memory to 1GB
)
def retrieve_search_queries(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for retrieving user queries (used for telegram bot pagination)

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    # TODO remove for prod setup
    #Set CORS headers for the preflight request
    if req.method == 'OPTIONS':
        # Allows GET and POST requests from any origin with the Content-Type
        # header and caches preflight response for an hour
        headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': 'http://localhost:3000'
    }


    firebase_manager = create_firebase_manager()

    if not req.method == "GET":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only GET is supported"}),
            status=405,
            mimetype="application/json",
        )

    splitted_path = req.path.split("/")
    session_id = splitted_path[1] if len(splitted_path) == 2 else None

    if not session_id:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid path parameters, please provide session id"}),
            status=400,
            mimetype="application/json",
            headers=headers
        )

    try:
        ref = firebase_manager.firestore_client.collection("userQuery").document(session_id)
        doc = ref.get()
    except Exception as e:
        logger.exception("Unable to fetch schemes search results from firestore", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error, unable to fetch schemes search results from firestore"}),
            status=500,
            mimetype="application/json",
            headers=headers
        )

    if not doc.exists:
        return https_fn.Response(
            response=json.dumps({"error": "Search query with provided session id does not exist"}),
            status=404,
            mimetype="application/json",
            headers=headers
        )

    results = {"data": doc.to_dict()}
    return https_fn.Response(
        response=json.dumps(results),
        status=200,
        mimetype="application/json",
        headers=headers)
