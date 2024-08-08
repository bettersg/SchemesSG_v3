from fastapi import FastAPI, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from contextlib import asynccontextmanager

from transformers import AutoModel, AutoTokenizer
import faiss
from ml_logic.model import combine_and_aggregate_results
from ml_logic.preprocessing import split_query_into_needs

ml_models = {}

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield
    # Clean up the ML models and release the resources
    ml_models.clear()


app = FastAPI(lifespan=lifespan)
# Assuming you've saved your model and tokenizer to the same path

# # Allow all requests (optional, good for development purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class PredictParams(BaseModel):
    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[int] = 0


async def get_predict_params(request: Request):
    # Attempt to parse the parameters from the query string
    query_params = request.query_params
    query = query_params.get("query")
    top_k = query_params.get("top_k", 20)
    similarity_threshold = query_params.get("similarity_threshold", 0)

    # If the query is not present in the query string, parse from the JSON body
    if query is None:
        try:
            body = await request.json()
            query = body.get("query")
            top_k = body.get("top_k", 20)
            similarity_threshold = body.get("similarity_threshold", 0)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")

    # Ensure query is present
    if query is None:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    return PredictParams(
        query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold)
    )


@app.get("/")
def index():
    return {"status": "ok"}


@app.get("/schemespredict")
@app.post("/schemespredict")
async def predict(params: PredictParams = Depends(get_predict_params)):
    query = params.query
    top_k = params.top_k
    similarity_threshold = params.similarity_threshold

    print(query)  # query text provided by the user
    print(top_k)  # how many top schemes to search based on the query
    print(
        similarity_threshold
    )  # indicate the schemes similarity threshold from 0 to 4. 5 levels.

    split_needs = split_query_into_needs(query)
    final_results = combine_and_aggregate_results(
        split_needs, ml_models, query, top_k, similarity_threshold
    )
    # result = search_similar_items(query, ml_models)
    results_json = {"data": final_results.to_dict(orient="records"), "mh": 0.7}
    # results_json = final_results.to_dict(orient='records')
    return results_json
