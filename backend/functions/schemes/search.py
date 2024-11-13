"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemes_search
"""

import json

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn
from loguru import logger

from ml_logic import PredictParams, SearchModel


search_model = None


def init_model():
    """Initialises SearchModel class"""

    global search_model

    firebase_manager = FirebaseManager()
    search_model = SearchModel(firebase_manager)


@https_fn.on_request(region="asia-southeast1")
def schemes_search(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for schemes search endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    global search_model

    if not search_model:
        init_model()

    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST or GET is supported"}),
            status=405,
            mimetype="application/json",
        )

    try:
        body = req.get_json(silent=True)
        query = body.get("query", None)
        top_k = body.get("top_k", 20)
        similarity_threshold = body.get("similarity_threshold", 0)
        # print(query, top_k, similarity_threshold)
    except Exception:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}), status=400, mimetype="application/json"
        )

    if query is None:
        return https_fn.Response(
            response=json.dumps({"error": "Parameter 'query' in body is required"}),
            status=400,
            mimetype="application/json",
        )

    params = PredictParams(query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold))

    try:
        results = search_model.predict(params)
    except Exception as e:
        logger.exception("Error searching schemes", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}), status=500, mimetype="application/json"
        )

    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json")
