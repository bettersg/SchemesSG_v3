"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/retrieve_search_queries
"""

import json

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from utils.cors_config import get_cors_headers, handle_cors_preflight
from utils.auth import verify_auth_token


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
    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    headers = get_cors_headers(req)

    # Verify authentication
    is_valid, auth_message = verify_auth_token(req)
    if not is_valid:
        return https_fn.Response(
            response=json.dumps({"error": f"Authentication failed: {auth_message}"}),
            status=401,
            mimetype="application/json",
            headers=headers,
        )

    firebase_manager = create_firebase_manager()

    if not req.method == "GET":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only GET is supported"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    splitted_path = req.path.split("/")
    session_id = splitted_path[1] if len(splitted_path) == 2 else None

    # Check if this is a warmup request from the query parameters
    is_warmup = req.args.get("is_warmup", "false").lower() == "true"

    if not session_id:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid path parameters, please provide session id"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    # For warmup requests, return success immediately without database operations
    if is_warmup:
        return https_fn.Response(
            response=json.dumps({"message": "Warmup request successful"}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    try:
        ref = firebase_manager.firestore_client.collection("userQuery").document(session_id)
        doc = ref.get()
    except Exception as e:
        logger.exception("Unable to fetch schemes search results from firestore", e)
        return https_fn.Response(
            response=json.dumps(
                {"error": "Internal server error, unable to fetch schemes search results from firestore"}
            ),
            status=500,
            mimetype="application/json",
            headers=headers,
        )

    if not doc.exists:
        return https_fn.Response(
            response=json.dumps({"error": "Search query with provided session id does not exist"}),
            status=404,
            mimetype="application/json",
            headers=headers,
        )

    results = {"data": doc.to_dict()}
    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json", headers=headers)
