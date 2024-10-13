"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/schemespredict
"""

import json
import os
from collections import defaultdict
from typing import Optional

import faiss
import numpy as np
from firebase_functions import https_fn
from pydantic import BaseModel

from ml_logic.model import combine_and_aggregate_results
from ml_logic.preprocessing import split_query_into_needs
from transformers import AutoModel, AutoTokenizer


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
ml_models = {}
top_schemes = defaultdict(lambda: {})


def init():
    # Load the ML model
    model_path = "ml_logic/schemesv2-torch-allmpp-model"
    tokenizer_path = "ml_logic/schemesv2-torch-allmpp-tokenizer"

    # Load the embeddings and index
    ml_models["model"] = AutoModel.from_pretrained(model_path)
    ml_models["tokenizer"] = AutoTokenizer.from_pretrained(tokenizer_path)
    print("got model")
    ml_models["embeddings"] = np.load("ml_logic/schemesv2-your_embeddings.npy")
    ml_models["index"] = faiss.read_index("ml_logic/schemesv2-your_index.faiss")
    print("got embedding and index")

    # Clean up the ML models and release the resources
    # ml_models.clear()
    # top_schemes.clear()


class PredictParams(BaseModel):
    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[int] = 0
    session_id: str


def predict(params: PredictParams):
    global top_schemes, ml_models

    query = params.query
    top_k = params.top_k
    similarity_threshold = params.similarity_threshold
    session_id = params.session_id

    # print(query)  # query text provided by the user
    # print(top_k)  # how many top schemes to search based on the query
    # print(similarity_threshold)  # indicate the schemes similarity threshold from 0 to 4. 5 levels.

    split_needs = split_query_into_needs(query)
    final_results = combine_and_aggregate_results(split_needs, ml_models, query, top_k, similarity_threshold)
    # result = search_similar_items(query, ml_models)
    results_json = {"data": final_results.to_dict(orient="records"), "mh": 0.7}
    # results_json = final_results.to_dict(orient='records')
    top_schemes[session_id] = results_json
    return results_json


init()


@https_fn.on_request(region="asia-southeast1")
def schemespredict(req: https_fn.Request) -> https_fn.Response:
    global ml_models

    if not ml_models:
        init()

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
        results = predict(params)
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
