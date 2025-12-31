"""
Firestore client for Cloud Run service.

Provides connection to Firestore for reading/writing scheme data.
"""
import os
from typing import Optional

from firebase_admin import firestore, credentials, initialize_app
from loguru import logger

_db = None


def get_firestore_client():
    """
    Get or create Firestore client.

    Uses Firebase Admin SDK credentials from environment variables.
    """
    global _db
    if _db is not None:
        return _db

    try:
        private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")

        if not private_key or not os.getenv("FB_PROJECT_ID"):
            logger.warning("Firebase credentials not configured")
            return None

        cred = credentials.Certificate({
            "type": os.getenv("FB_TYPE", "service_account"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FB_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv(
                "FB_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        })

        initialize_app(cred)
        _db = firestore.client()
        logger.info(f"Connected to Firestore: {os.getenv('FB_PROJECT_ID')}")
        return _db

    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        return None


def update_scheme_entry(db, doc_id: str, data: dict) -> bool:
    """
    Update schemeEntries document.

    Args:
        db: Firestore client
        doc_id: Document ID in schemeEntries collection
        data: Fields to update

    Returns:
        True if successful, False otherwise
    """
    if db is None:
        logger.warning("Firestore not available, skipping update")
        return False

    try:
        entry_ref = db.collection("schemeEntries").document(doc_id)
        entry_ref.update(data)
        return True
    except Exception as e:
        logger.error(f"Failed to update schemeEntries/{doc_id}: {e}")
        return False
