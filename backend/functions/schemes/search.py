"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search
"""

import json

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from ml_logic import PaginatedSearchParams, SearchModel
from utils.auth import verify_auth_token
from utils.cors_config import get_cors_headers, handle_cors_preflight


def create_search_model() -> SearchModel:
    """Factory function to create a SearchModel instance."""
    firebase_manager = FirebaseManager()
    return SearchModel(firebase_manager)


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
)
def schemes_search(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for schemes search endpoint with pagination

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

    search_model = create_search_model()

    if not req.method == "POST":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST is supported"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    try:
        body = req.get_json(silent=True)
        query = body.get("query", None)
        limit = body.get("limit", 20)
        cursor = body.get("cursor", None)
        similarity_threshold = body.get("similarity_threshold", 0)
        is_warmup = body.get("is_warmup", False)
        top_k = body.get("top_k", 100)
        filters = body.get("filters", None)
    except Exception:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    if query is None:
        return https_fn.Response(
            response=json.dumps({"error": "Parameter 'query' in body is required"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    params = PaginatedSearchParams(
        query=query,
        limit=int(limit),
        cursor=cursor,
        similarity_threshold=int(similarity_threshold),
        is_warmup=is_warmup,
        top_k=int(top_k),
        filters=filters,
    )

    try:
        results = search_model.predict_paginated(params)
        return https_fn.Response(
            response=json.dumps(results),
            status=200,
            mimetype="application/json",
            headers=headers,
        )
    except Exception as e:
        logger.exception("Error searching schemes", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error searching schemes"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )
