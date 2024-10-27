"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemespredict
"""

import json

from firebase_admin import firestore
from firebase_functions import https_fn

from ml_logic.modelManager import PredictParams, SearchModel


search_model = None


@https_fn.on_request(region="asia-southeast1")
def schemespredict(req: https_fn.Request) -> https_fn.Response:
    global search_model

    if not search_model:
        db = firestore.client()
        search_model = SearchModel(db)

    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response = json.dumps({'error': 'Invalid request method; only POST or GET is supported'}),
            status = 405,
            mimetype = 'application/json'
        )

    try:
        body = req.get_json(silent=True)
        session_id = body.get("sessionID", None)
        query = body.get("query", None)
        top_k = body.get("top_k", 20)
        similarity_threshold = body.get("similarity_threshold", 0)
        #print(session_id, query, top_k, similarity_threshold)
    except Exception:
        return https_fn.Response(
            response = json.dumps({'error': 'Invalid request body'}),
            status = 400,
            mimetype = 'application/json'
        )

    if query is None:
        return https_fn.Response(
            response = json.dumps({'error': "Parameter \'query\' in body is required"}),
            status = 400,
            mimetype = 'application/json'
        )

    params = PredictParams(
        query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold), session_id=str(session_id)
    )

    try:
        results = search_model.predict(params)
    except Exception:
        return https_fn.Response(
            response = json.dumps({'error': 'Internal server error'}),
            status = 500,
            mimetype = 'application/json'
        )

    return https_fn.Response(
            response = json.dumps(results),
            status = 200,
            mimetype = 'application/json'
        )
