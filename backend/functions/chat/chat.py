"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/chat_message
"""

import json
import sys
import time
from datetime import datetime

import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from ml_logic import Chatbot, dataframe_to_text


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
    start_time = time.time()
    logger.info(f"[{datetime.now()}] Request received")

    # TODO remove for prod setup
    # Set CORS headers for the preflight request
    if req.method == "OPTIONS":
        # Allows GET and POST requests from any origin with the Content-Type
        # header and caches preflight response for an hour
        headers = {
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        logger.info(f"[{datetime.now()}] OPTIONS request handled in {(time.time() - start_time)*1000:.2f}ms")
        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "http://localhost:3000"}
    if not (req.method == "POST" or req.method == "GET"):
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST or GET is supported"}),
            status=405,
            mimetype="application/json",
        )
    chatbot_start = time.time()
    chatbot = create_chatbot()
    logger.info(f"[{datetime.now()}] Chatbot creation took {(time.time() - chatbot_start)*1000:.2f}ms")

    try:
        json_start = time.time()
        data = req.get_json(silent=True)
        input_text = data.get("message")
        session_id = data.get("sessionID")
        stream = data.get("stream", False)  # new parameter to indicate streaming
        top_schemes_text = ""
        logger.info(f"[{datetime.now()}] JSON parsing took {(time.time() - json_start)*1000:.2f}ms")
    except Exception:
        logger.error(f"[{datetime.now()}] JSON parsing failed")
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    try:
        firestore_start = time.time()
        ref = chatbot.firebase_manager.firestore_client.collection("userQuery").document(session_id)
        doc = ref.get()
        logger.info(f"[{datetime.now()}] Firestore fetch took {(time.time() - firestore_start)*1000:.2f}ms")
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
        df_start = time.time()
        doc_dict = doc.to_dict()
        query_text = doc_dict.get("query_text", "")
        df = pd.DataFrame(doc_dict["schemes_response"])
        top_schemes_text = dataframe_to_text(df)
        logger.info(f"[{datetime.now()}] DataFrame processing took {(time.time() - df_start)*1000:.2f}ms")

        if stream:
            stream_start = time.time()

            def generate():
                for chunk in chatbot.chatbot_stream(
                    top_schemes_text=top_schemes_text,
                    input_text=input_text,
                    session_id=session_id,
                    query_text=query_text,
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            logger.info(f"[{datetime.now()}] Stream setup took {(time.time() - stream_start)*1000:.2f}ms")

            return https_fn.Response(
                response=generate(),
                status=200,
                mimetype="text/event-stream",
                headers={
                    "Access-Control-Allow-Origin": "http://localhost:3000",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                },
            )
        else:
            chatbot_process_start = time.time()
            results = chatbot.chatbot(
                top_schemes_text=top_schemes_text, input_text=input_text, session_id=session_id, query_text=query_text
            )
            logger.info(
                f"[{datetime.now()}] Chatbot processing took {(time.time() - chatbot_process_start)*1000:.2f}ms"
            )

    except Exception as e:
        logger.exception("Error with chatbot", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )

    total_time = time.time() - start_time
    logger.info(f"[{datetime.now()}] Total request processing took {total_time*1000:.2f}ms")

    return https_fn.Response(response=json.dumps(results), status=200, mimetype="application/json", headers=headers)
