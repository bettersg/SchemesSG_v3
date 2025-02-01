"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/keep_search_warm
"""

import json
import os

import requests
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options, scheduler_fn
from loguru import logger
from ml_logic import PredictParams, SearchModel
from utils.cors_config import get_cors_headers, handle_cors_preflight


def create_search_model() -> SearchModel:
    """Factory function to create a SearchModel instance."""
    firebase_manager = FirebaseManager()
    return SearchModel(firebase_manager)


def get_search_endpoint_url() -> str:
    """Get the appropriate search endpoint URL based on environment."""
    env = os.getenv("ENVIRONMENT", "local")
    logger.info(f"Current environment: {env}")

    if env == "local":
        host = os.getenv("FUNCTIONS_HOST", "127.0.0.1")
        port = os.getenv("FUNCTIONS_PORT", "5001")
        return f"http://{host}:{port}/schemessg-v3-dev/asia-southeast1/schemes_search"
    elif env == "staging":
        return "https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/schemes_search"
    else:  # prod
        return "https://asia-southeast1-schemessg.cloudfunctions.net/schemes_search"


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
)
def schemes_search(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for schemes search endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    headers = get_cors_headers(req)
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
        top_k = body.get("top_k", 20)
        similarity_threshold = body.get("similarity_threshold", 0)
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

    params = PredictParams(query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold))

    try:
        results = search_model.predict(params)
    except Exception as e:
        logger.exception("Error searching schemes", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )

    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json", headers=headers)


@scheduler_fn.on_schedule(
    schedule="*/4 * * * *",  # Run every 4 minutes
    region="asia-southeast1",
    memory=options.MemoryOption.MB_256,
    concurrency=1,  # Only allow one instance at a time
    min_instances=0,  # Don't keep instances warm
    max_instances=1,  # Maximum one instance
    retry_count=0,  # Don't retry on failure
)
def keep_search_warm(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scheduled function to keep the search model warm by making a simple search request.
    This helps reduce cold starts for the main search endpoint.

    Args:
        event (scheduler_fn.ScheduledEvent): The event object
    """
    try:
        url = get_search_endpoint_url()
        logger.info(f"Making warm-up request to: {url}")

        # Make a POST request to the endpoint
        response = requests.post(
            url,
            json={"query": "education", "top_k": 1, "similarity_threshold": 0},
            headers={"Content-Type": "application/json"},
            timeout=30,  # Add timeout to prevent hanging
        )

        if response.status_code == 200:
            logger.info("Successfully kept search endpoint warm")
            return None  # Explicitly return None for success
        else:
            logger.error(f"Failed to keep search endpoint warm. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None  # Explicitly return None even for failure

    except requests.exceptions.Timeout:
        logger.error("Timeout while trying to keep search endpoint warm")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while trying to keep search endpoint warm")
        return None
    except Exception as e:
        logger.exception("Error in keep_search_warm function", e)
        return None  # Return None instead of raising the exception
