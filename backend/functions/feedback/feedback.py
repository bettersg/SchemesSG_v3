"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/feedback
"""

from firebase_functions import https_fn
from firebase_admin import firestore
from uuid import uuid4
from datetime import timezone 
import datetime 

# Firestore client
db = firestore.client()

# Firestore collection name
COLLECTION_NAME = "schemeEntries"

@https_fn.on_request(region="asia-southeast1")
def feedback(req: https_fn.Request) -> https_fn.Response:
    if req.method != "POST":
        return https_fn.Response("Only POST requests are allowed.", status=405)

    try:
        # Parse the request data
        request_json = req.get_json()
        feedback_text = request_json.get("feedbackText")
        timestamp = datetime.datetime.now(timezone.utc) 

        if not feedback_text or not timestamp:
            return {"success": False, "message": "Missing required fields."}, 400

        # Generate a UUID
        request_uuid = str(uuid4())

        # Prepare the data for Firestore
        feedback_data = {
            "feedbackText": feedback_text,
            "timestamp": timestamp,
            "requestUUID": request_uuid,
        }

        # Add the data to Firestore
        db.collection(COLLECTION_NAME).add(feedback_data)

        # Return a success response
        return {"success": True, "message": "Feedback successfully added."}, 200

    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": "Failed to add feedback."}, 500
