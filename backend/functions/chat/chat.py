"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message
"""

import json
import sys
from datetime import datetime

import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from ml_logic import Chatbot, dataframe_to_text
from utils.cors_config import get_cors_headers, handle_cors_preflight


# Remove default handler
logger.remove()

# Add custom handler with async writing
logger.add(
    sys.stderr,
    level="INFO",  # Set to "DEBUG" in development
    enqueue=True,  # Enable async logging
    backtrace=False,  # Disable traceback for better performance
    diagnose=False,  # Disable diagnosis for better performance
)


def create_chatbot():
    """Factory function to create a Chatbot instance."""
    if not Chatbot.initialised:
        firebase_manager = FirebaseManager()
        return Chatbot(firebase_manager)
    return Chatbot._instance


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
    logger.info("Request received")

    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    headers = get_cors_headers(req)

    if not req.method == "POST":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST or GET is supported"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    chatbot = create_chatbot()

    try:
        data = req.get_json(silent=True)
        input_text = data.get("message")
        session_id = data.get("sessionID")
        stream = data.get("stream", False)  # new parameter to indicate streaming
        top_schemes_text = ""
    except Exception:
        logger.error(f"[{datetime.now()}] JSON parsing failed")
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}),
            status=400,
            mimetype="application/json",
            headers=headers,
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
            headers=headers,
        )

    if not doc.exists:
        logger.warning(f"[{datetime.now()}] Session ID {session_id} not found")
        return https_fn.Response(
            response=json.dumps({"error": "Search query with sessionID does not exist"}),
            status=404,
            mimetype="application/json",
            headers=headers,
        )

    try:
        doc_dict = doc.to_dict()
        query_text = doc_dict.get("query_text", "")
        df = pd.DataFrame(doc_dict["schemes_response"])
        top_schemes_text = dataframe_to_text(df)

        if stream:

            def generate():
                for chunk in chatbot.chatbot_stream(
                    top_schemes_text=top_schemes_text,
                    input_text=input_text,
                    session_id=session_id,
                    query_text=query_text,
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            cors_headers = get_cors_headers(req)
            headers = {
                **cors_headers,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }

            return https_fn.Response(
                response=generate(),
                status=200,
                mimetype="text/event-stream",
                headers=headers,
            )
        else:
            results = chatbot.chatbot(
                top_schemes_text=top_schemes_text, input_text=input_text, session_id=session_id, query_text=query_text
            )

    except Exception as e:
        logger.exception("Error with chatbot", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )

    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json", headers=headers)
