from typing import Tuple
from firebase_admin import auth
from firebase_functions import https_fn
from loguru import logger


def verify_auth_token(req: https_fn.Request) -> Tuple[bool, str]:
    """Verify Firebase Auth token from request headers."""
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False, "No valid authorization header"

    try:
        token = auth_header.split("Bearer ")[1]
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)
        return True, decoded_token["uid"]
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return False, "Token verification failed"
