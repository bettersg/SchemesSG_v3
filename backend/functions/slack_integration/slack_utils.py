"""
Slack utility functions for Firebase Functions.

This module provides Slack-specific utilities including signature verification
for securing Slack interactive component requests.
"""

import hashlib
import hmac
import os
import time

from dotenv import load_dotenv
from firebase_functions import https_fn


# Load environment variables (for local development)
# Loads from functions/.env file
load_dotenv()


def get_slack_signing_secret() -> bytes:
    """
    Get Slack signing secret from environment variables.

    Supports both local (.env) and production (Firebase secrets) environments.

    Returns:
        Signing secret as bytes, or empty bytes if not found
    """
    secret = os.getenv("SLACK_SIGNING_SECRET", "")
    return secret.encode() if secret else b""


def verify_slack_signature(req: https_fn.Request) -> bool:
    """
    Verify that a request from Slack is authentic using HMAC signature verification.

    This implements Slack's request signature verification as described in:
    https://api.slack.com/authentication/verifying-requests-from-slack

    Args:
        req: Firebase Function request object

    Returns:
        True if signature is valid, False otherwise
    """
    # Get timestamp from headers
    timestamp = req.headers.get("X-Slack-Request-Timestamp", "0")

    # Check if request is too old (replay attack protection)
    # Slack recommends rejecting requests older than 5 minutes
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - request_time) > 60 * 5:
            return False
    except (ValueError, TypeError):
        return False

    # Get raw request body
    # Firebase Functions: get_data() returns bytes, need to decode to string
    try:
        body_bytes = req.get_data()
        body = body_bytes.decode("utf-8")
    except Exception:
        return False

    # Build signature base string: v0:timestamp:body
    sig_basestring = f"v0:{timestamp}:{body}".encode()

    # Get signing secret
    signing_secret = get_slack_signing_secret()
    if not signing_secret:
        return False

    # Compute expected signature
    expected_sig = "v0=" + hmac.new(signing_secret, sig_basestring, hashlib.sha256).hexdigest()

    # Get actual signature from headers
    slack_sig = req.headers.get("X-Slack-Signature", "")

    # Compare signatures using constant-time comparison (prevents timing attacks)
    return hmac.compare_digest(expected_sig, slack_sig)
