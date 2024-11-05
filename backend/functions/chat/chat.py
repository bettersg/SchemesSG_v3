"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message
"""

import json

import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn

from ml_logic import Chatbot, dataframe_to_text


firebase_manager = FirebaseManager()
chatbot = None


def init_chatbot():
    """Initialises Chatbot class"""

    global chatbot

    firebase_manager = FirebaseManager()
    chatbot = Chatbot(firebase_manager)


# change endpoint later
@https_fn.on_request(region="asia-southeast1")
def chat_message(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for chat message endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """

    global firebase_manager
    global chatbot

    if not chatbot:
        init_chatbot()

    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST or GET is supported"}),
            status=405,
            mimetype="application/json",
        )

    try:
        data = req.get_json(silent=True)
        input_text = data.get("message")
        session_id = data.get("sessionID")
        top_schemes_text = ""
    except Exception:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}), status=400, mimetype="application/json"
        )

    try:
        ref = firebase_manager.firestore_client.collection("userQuery").document(session_id)
        doc = ref.get()
    except Exception as e:
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error, unable to fetch user query from firestore"}),
            status=500,
            mimetype="application/json",
        )

    if not doc.exists:
        return https_fn.Response(
            response=json.dumps({"error": "Search query with sessionID does not exist"}),
            status=404,
            mimetype="application/json",
        )


    df = pd.DataFrame(doc.to_dict()['schemes_response'])
    top_schemes_text = dataframe_to_text(df)

    try:
        results = chatbot.chatbot(top_schemes_text=top_schemes_text, input_text=input_text, session_id=session_id)
    except Exception:
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}), status=500, mimetype="application/json"
        )

    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json")
