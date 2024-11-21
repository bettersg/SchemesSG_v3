"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message
"""

import json

import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger

from ml_logic import Chatbot, dataframe_to_text


def create_chatbot():
    """Factory function to create a Chatbot instance."""
    firebase_manager = FirebaseManager()
    return Chatbot(firebase_manager)


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,  # Increases memory to 1GB
)
def chat_message(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for chat message endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    # TODO remove for prod setup
    #Set CORS headers for the preflight request
    if req.method == 'OPTIONS':
        # Allows GET and POST requests from any origin with the Content-Type
        # header and caches preflight response for an hour
        headers = {
            'Access-Control-Allow-Origin': 'http://localhost:3000',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': 'http://localhost:3000'
    }
    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST or GET is supported"}),
            status=405,
            mimetype="application/json",
        )
    chatbot = create_chatbot()

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
        ref = chatbot.firebase_manager.firestore_client.collection("userQuery").document(session_id)
        doc = ref.get()
    except Exception as e:
        logger.exception("Unable to fetch user query from firestore", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error, unable to fetch user query from firestore"}),
            status=500,
            mimetype="application/json",
            headers=headers
        )

    if not doc.exists:
        return https_fn.Response(
            response=json.dumps({"error": "Search query with sessionID does not exist"}),
            status=404,
            mimetype="application/json",
            headers=headers
        )

    try:
        df = pd.DataFrame(doc.to_dict()["schemes_response"])
        top_schemes_text = dataframe_to_text(df)
        results = chatbot.chatbot(top_schemes_text=top_schemes_text, input_text=input_text, session_id=session_id)
    except Exception as e:
        logger.exception("Error with chatbot", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json",
            headers=headers
        )

    return https_fn.Response(
        response=json.dumps(results),
        status=200,
        mimetype="application/json",
        headers=headers)
