"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/feedback
"""

import json
from datetime import datetime, timezone

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
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
