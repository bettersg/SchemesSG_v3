"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chatbot
"""

import json

import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn

from fast_api.cleantext import clean_scraped_text
from ml_logic.modelManager import SearchModel


firebase_manager = FirebaseManager()
search_model = None


def init_model():
    """Initialises SearchModel class"""

    global search_model

    firebase_manager = FirebaseManager()
    search_model = SearchModel(firebase_manager)

def dataframe_to_text(df):
    text_summary = ''
    for _, row in df.iterrows():
        row = row.data
        cleanScrape = row['Scraped Text']
        sentence = clean_scraped_text(cleanScrape)

        text_summary += f"Scheme Name: {row['Scheme']}, Agency: {row['Agency']}, Description: {row['Description']}, Link: {row['Link']}, Scraped Text from website: {sentence}\n"
    return text_summary


@https_fn.on_request(region="asia-southeast1")
def message(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for chat message endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    global firebase_manager
    global search_model

    if not search_model:
        init_model()

    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response = json.dumps({'error': 'Invalid request method; only POST or GET is supported'}),
            status = 405,
            mimetype = 'application/json')

    try:
        data = req.get_json(silent=True)
        input_text = data.get('message')
        session_id = data.get('sessionID')
        top_schemes_text = ""
    except Exception:
        return https_fn.Response(
            response = json.dumps({'error': 'Invalid request body'}),
            status = 400,
            mimetype = 'application/json'
        )

    doc = firebase_manager.firestore_client.collection('userQuery').document(session_id)
    if not doc.exists:
        return https_fn.Response(
            response = json.dumps({"error": "Search query with sessionID does not exist"}),
            status = 404,
            mimetype = 'application/json'
        )

    df = pd.DataFrame(doc.to_dict())
    if df:
        top_schemes_text = dataframe_to_text(df)

    try:
        results = search_model.chatbot(top_schemes_text=top_schemes_text, input_text=input_text, session_id=session_id)
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
