"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/feedback
"""

import json
from datetime import datetime, timezone

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from google.cloud import firestore
from utils.auth import verify_auth_token
from utils.cors_config import get_cors_headers, handle_cors_preflight


# Firestore client
firebase_manager = FirebaseManager()


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
)
def feedback(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for logging user feedback

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    # Handle CORS preflight request
    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    # Get CORS headers based on request origin
    headers = get_cors_headers(req)

    # Verify authentication
    is_valid, auth_message = verify_auth_token(req)
    if not is_valid:
        return https_fn.Response(
            response=json.dumps({"error": f"Authentication failed: {auth_message}"}),
            status=401,
            mimetype="application/json",
            headers=headers,
        )

    if req.method != "POST":
        return https_fn.Response(
            response=json.dumps({"success": False, "message": "Only POST requests are allowed"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    try:
        # Parse the request data
        request_json = req.get_json()
        feedback_text = request_json.get("feedbackText")
        userName = request_json.get("userName")
        userEmail = request_json.get("userEmail")
        is_warmup = request_json.get("is_warmup", False)
        timestamp = datetime.now(timezone.utc)

        # For warmup requests, return success immediately without database operations
        if is_warmup:
            return https_fn.Response(
                response=json.dumps({"success": True, "message": "Warmup request successful"}),
                status=200,
                mimetype="application/json",
                headers=headers,
            )

        # Thumbs up/down on a chat response. Stored separately from free-text
        # feedback as a per-session map keyed by message index, so a repeated
        # click can overwrite and an undo (rating=None) can clear the entry.
        if request_json.get("source") == "chat" and "messageIndex" in request_json:
            session_id = request_json.get("sessionId")
            message_index = request_json.get("messageIndex")
            rating = request_json.get("rating")  # "up", "down", or None to undo
            if not session_id or not isinstance(message_index, int) or rating not in ("up", "down", None):
                return https_fn.Response(
                    response=json.dumps({"success": False, "message": "Invalid rating payload"}),
                    status=400,
                    mimetype="application/json",
                    headers=headers,
                )

            doc_ref = firebase_manager.firestore_client.collection("chatRatings").document(session_id)
            field = f"ratings.{message_index}"
            value = firestore.DELETE_FIELD if rating is None else rating
            doc_ref.set({"sessionId": session_id, "updated": timestamp}, merge=True)
            doc_ref.update({field: value})

            return https_fn.Response(
                response=json.dumps({"success": True, "message": "Rating recorded"}),
                status=200,
                mimetype="application/json",
                headers=headers,
            )

        if not feedback_text:
            return https_fn.Response(
                response=json.dumps({"success": False, "message": "Missing required fields"}),
                status=400,
                mimetype="application/json",
                headers=headers,
            )

        # Prepare the data for Firestore
        feedback_data = {
            "feedbackText": feedback_text,
            "timestamp": timestamp,
            "userName": userName,
            "userEmail": userEmail,
        }

        # Add the data to Firestore
        firebase_manager.firestore_client.collection("userFeedback").add(feedback_data)

        # Return a success response
        return https_fn.Response(
            response=json.dumps({"success": True, "message": "Feedback successfully added"}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    except Exception as e:
        print(f"Error: {e}")
        return https_fn.Response(
            response=json.dumps({"success": False, "message": "Failed to add feedback"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )
