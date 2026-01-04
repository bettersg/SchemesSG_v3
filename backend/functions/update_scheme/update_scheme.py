"""
url for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/update_scheme

Note: In local dev (without Firestore emulator), triggers don't fire.
So we call the pipeline directly after creating the document.
In production, the Firestore trigger will handle it.
"""

import json
import os
import threading
from datetime import datetime, timezone

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from utils.auth import verify_auth_token
from utils.cors_config import get_cors_headers, handle_cors_preflight


# Firestore client
firebase_manager = FirebaseManager()


def is_local_dev() -> bool:
    """Check if running in local development (emulator without Firestore emulator)."""
    # If FIRESTORE_EMULATOR_HOST is not set, we're connecting to cloud Firestore
    # and triggers won't work, so we need to call the pipeline directly
    return os.getenv("FIRESTORE_EMULATOR_HOST") is None and os.getenv("ENVIRONMENT") == "local"


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,  # Increased for pipeline processing in local dev
)
def update_scheme(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for users seeking to add new schemes or request an edit on an existing scheme

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

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
        changes = request_json.get("Changes")
        description = request_json.get("Description")
        link = request_json.get("Link")
        scheme = request_json.get("Scheme")
        status = request_json.get("Status")
        entryId = request_json.get("entryId")
        userName = request_json.get("userName")
        userEmail = request_json.get("userEmail")
        typeOfRequest = request_json.get("typeOfRequest")
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
            "userEmail": userEmail,
            "typeOfRequest": typeOfRequest,
        }

        # Add the data to Firestore
        _, doc_ref = firebase_manager.firestore_client.collection("schemeEntries").add(update_scheme_data)
        doc_id = doc_ref.id
        logger.info(f"Created schemeEntries document: {doc_id}")

        # In local dev mode (without Firestore emulator), triggers don't fire
        # So we call the pipeline in a background thread for new scheme submissions
        if is_local_dev() and typeOfRequest and typeOfRequest.lower() == "new":
            logger.info(f"Local dev mode: calling pipeline in background for {doc_id}")

            def run_pipeline():
                try:
                    from new_scheme.trigger_new_scheme_pipeline import process_new_scheme_entry

                    process_new_scheme_entry(doc_id, update_scheme_data)
                except Exception as pipeline_error:
                    logger.error(f"Pipeline error for {doc_id}: {pipeline_error}")

            thread = threading.Thread(target=run_pipeline, daemon=True)
            thread.start()

        # Return a success response
        return https_fn.Response(
            response=json.dumps(
                {"success": True, "message": "Request for scheme update successfully added", "docId": doc_id}
            ),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    except Exception as e:
        print(f"Error: {e}")
        return https_fn.Response(
            response=json.dumps({"success": False, "message": "Failed to add request for scheme update"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )
