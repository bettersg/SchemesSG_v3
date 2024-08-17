import os
from dotenv import dotenv_values
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv.main import load_dotenv
import pandas as pd
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from contextlib import asynccontextmanager
from .cleantext import clean_scraped_text
from collections import defaultdict

from transformers import AutoModel, AutoTokenizer
import faiss
from ml_logic.model import combine_and_aggregate_results
from ml_logic.preprocessing import split_query_into_needs
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

ml_models = {}
llm = None
chat_history = {}
top_schemes = defaultdict(lambda: {})

class Config:
    def __init__(self):
        load_dotenv()

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr

def init_chatbot():
    config = Config()
    return AzureChatOpenAI(
                deployment_name=config.deployment, 
                azure_endpoint=config.endpoint, 
                openai_api_version=config.version, 
                openai_api_key=config.apikey, 
                openai_api_type=config.type, 
                model_name=config.model,
                temperature=0.3
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm 
    llm = init_chatbot()
    print('got chatbot llm')
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
    chat_history.clear()
    top_schemes.clear()


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
    session_id: str


async def get_predict_params(request: Request):
    try:
        body = await request.json()
        session_id = body.get("sessionID")
        query = body.get("query")
        top_k = body.get("top_k", 20)
        similarity_threshold = body.get("similarity_threshold", 0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")

    # Ensure query is present
    if query is None:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    return PredictParams(
        query=query, top_k=int(top_k), similarity_threshold=int(similarity_threshold), session_id=str(session_id)
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
    session_id = params.session_id

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
    top_schemes[session_id] = results_json
    return results_json


def get_session_history(session_id: str):
    global chat_history
    ai_message = """
    🌟 Welcome to Scheme Support Chat! 🌟 Feel free to ask me questions like:
    - "Can you tell me more about Scheme X?"
    - "How can I apply for support from Scheme X?"

    To get started, just type your question below. I'm here to help explore schemes results 🚀
    """
    if session_id not in chat_history:
        chat_history[session_id] = ChatMessageHistory(messages=[AIMessage(ai_message)])

    return chat_history[session_id]

def dataframe_to_text(df):
    # Example function to convert first 5 rows of a DataFrame into a text summary
    text_summary = ''
    for index, row in df.iterrows():
        row = row.data
        cleanScrape = row['Scraped Text']
        sentence = clean_scraped_text(cleanScrape)

        text_summary += f"Scheme Name: {row['Scheme']}, Agency: {row['Agency']}, Description: {row['Description']}, Link: {row['Link']}, Scraped Text from website: {sentence}\n"
    return text_summary


@app.post('/chatbot')
async def chatbot(request: Request):
    global chat_history
    try:
        data = await request.json()
        input_text = data.get('message')
        session_id = data.get('sessionID')
        top_schemes_text = ""

        df = pd.DataFrame(top_schemes[session_id])
        if df is not None:
            top_schemes_text = dataframe_to_text(df)

        template_text = """
        As a virtual assistant, I'm dedicated to helping user navigate through the available schemes. User has done initial search based on their needs and system has provided top schemes relevant to the search. Now, my job is to advise on the follow up user queries based on the schemes data available by analyzing user query and extracting relevant answers from the top scheme data. Top Schemes Information includes scheme name, agency, Link to website, and may include text directly scraped from scheme website.

        In responding to user queries, I will adhere to the following principles:

        1. **Continuity in Conversation**: Each new question may build on the ongoing conversation. I'll consider the chat history to ensure a coherent and contextual dialogue.

        2. **Role Clarity**: My purpose is to guide user by leveraging the scheme information provided. My responses aim to advise based on this data, without undertaking any actions outside these confines.

        3. **Language Simplicity**: I commit to using simple, accessible English, ensuring my responses are understandable to all users, without losing the essence or accuracy of the scheme information.

        4. **Safety and Respect**: Maintaining a safe, respectful interaction is paramount. I will not entertain or generate harmful, disrespectful, or irrelevant content. Should any query diverge from the discussion on schemes, I will gently redirect the focus back to how I can assist with scheme-related inquiries.

        5. **Avoidance of Fabrication**: My responses will solely rely on the information from the scheme details provided, avoiding any speculative or unfounded content. I will not alter or presume any specifics not clearly indicated in the scheme descriptions.

        **Top Schemes Information:**
        """ + top_schemes_text

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", template_text),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}"),
            ]
        )

        chain = prompt_template | llm
        chain_with_history = RunnableWithMessageHistory(
                chain,
                get_session_history,
                input_messages_key="query",
                history_messages_key="history"
            )
        
        config = {'configurable': {'session_id': session_id}}
        message = chain_with_history.invoke({"query": input_text}, config=config)
        return JSONResponse(content={"response": True, "message": message.content})

    except Exception as e:
        print(e)
        error_message = f'Error: {str(e)}'
        return JSONResponse(content={"response": False, "message": error_message})
    