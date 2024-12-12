"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/update_scheme
"""

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from datetime import datetime, timezone
import json

# Firestore client
firebase_manager = FirebaseManager()

@https_fn.on_request(
        region="asia-southeast1",
        memory=options.MemoryOption.GB_1,
    )
def update_scheme(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for users seeking to add new schemes or request an edit on an existing scheme

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    headers = {
        'Access-Control-Allow-Origin': 'http://localhost:3000'
    }
    if req.method != "POST":
        return https_fn.Response(
            response=json.dumps({"success": False, "message": "Only POST requests are allowed"}),
            status=405,
            mimetype="application/json",
            headers=headers
        )

    try:
        # Parse the request data
        request_json = req.get_json()
        changes = request_json.get("Changes")
        description = request_json.get("Description")
        link = request_json.get("Link")
        scheme = request_json.get("Scheme")
        status = request_json.get("Status")
        entryId = request_json.get("entryId")
        userName = request_json.get("userName")
        userEmail = request_json.get("userEmail")
        typeOfRequest = request_json.get("typeOfRequest")
        timestamp = datetime.now(timezone.utc)

        # Can use the below logic to have some null checks
        # if not feedback_text or not timestamp:
        #     return https_fn.Response(
        #         response=json.dumps({"success": False, "message": "Missing required feedbackText field"}),
        #         status=400,
        #         mimetype="application/json",
        #         headers=headers
        #     )

        # Prepare the data for Firestore
        update_scheme_data = {
            "Changes": changes,
            "Description": description,
            "Link": link,
            "Scheme": scheme,
            "Status": status,
            "entryId": entryId,
            "timestamp": timestamp,
            "userName": userName,
            "userEmail": userEmail
        }

        # Add the data to Firestore
        firebase_manager.firestore_client.collection("schemeEntries").add(update_scheme_data)

        # Return a success response
        return https_fn.Response(
            response=json.dumps({"success": True, "message": "Request for scheme update successfully added"}),
            status=200,
            mimetype="application/json",
            headers=headers
        )

    except Exception as e:
        print(f"Error: {e}")
        return https_fn.Response(
            response=json.dumps({"success": False, "message": "Failed to add request for scheme update"}),
            status=500,
            mimetype="application/json",
            headers=headers
        )
