import os
from dotenv import dotenv_values
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from langchain_openai import AzureChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from dotenv.main import load_dotenv, find_dotenv
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

class OpenAIConfig:
    def __init__(self):
        load_dotenv()

        for key, value in dotenv_values().items():
            setattr(self, key, value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    model_path = 'ml_logic/schemesv2-torch-allmpp-model'
    tokenizer_path = 'ml_logic/schemesv2-torch-allmpp-tokenizer'
    # Load the embeddings and index
    ml_models["model"] = AutoModel.from_pretrained(model_path)
    ml_models["tokenizer"] = AutoTokenizer.from_pretrained(tokenizer_path)
    print('got model')
    ml_models["embeddings"] = np.load('ml_logic/schemesv2-your_embeddings.npy')
    ml_models["index"] = faiss.read_index('ml_logic/schemesv2-your_index.faiss')
    print('got embedding and index')
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
    query = query_params.get('query')
    top_k = query_params.get('top_k', 20)
    similarity_threshold = query_params.get('similarity_threshold', 0)

    # If the query is not present in the query string, parse from the JSON body
    if query is None:
        try:
            body = await request.json()
            query = body.get('query')
            top_k = body.get('top_k', 20)
            similarity_threshold = body.get('similarity_threshold', 0)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")

    # Ensure query is present
    if query is None:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    return PredictParams(query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold))


@app.get("/")
def index():
    return {"status": "ok"}

@app.get('/schemespredict')
@app.post('/schemespredict')
async def predict(params: PredictParams = Depends(get_predict_params)):
    query = params.query
    top_k = params.top_k
    similarity_threshold = params.similarity_threshold

    print(query)  # query text provided by the user
    print(top_k)  # how many top schemes to search based on the query
    print(similarity_threshold)  # indicate the schemes similarity threshold from 0 to 4. 5 levels.

    split_needs = split_query_into_needs(query)
    final_results = combine_and_aggregate_results(split_needs, ml_models, query, top_k, similarity_threshold)
    # result = search_similar_items(query, ml_models)
    results_json= {
        "data": final_results.to_dict(orient='records'),
        "mh": 0.7
    }
    # results_json = final_results.to_dict(orient='records')
    return results_json


# TODO: incorrectly retains state across multiple clients. Look into RunnableWithMessageHistory
@app.post('/chatbot')
async def chatbot(request: Request):
    config = OpenAIConfig()

    try:
        data = await request.json()
        input_text = data.get('data')
        if not input_text:
            raise HTTPException(status_code=400, detail="No input data provided")
        
        llm = AzureChatOpenAI(
            deployment_name=config.deployment, 
            azure_endpoint=config.endpoint, 
            openai_api_version=config.version, 
            openai_api_key=config.apikey, 
            openai_api_type=config.type, 
            model_name=config.model,
            temperature=0
        )
        
        memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)
        conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
        output = conversation.predict(input=input_text)
        return JSONResponse(content={"response": True, "message": output})
    
    except Exception as e:
        print(e)
        error_message = f'Error: {str(e)}'
        return JSONResponse(content={"response": False, "message": error_message})
