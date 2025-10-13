"""
Utilities for cursor-based pagination in search endpoints.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional, Tuple

from loguru import logger


# Secret key for cursor signature
# In a production environment, this should be stored in environment variables
# or a secure configuration system
CURSOR_SECRET = os.environ.get("CURSOR_SECRET", "schemes_pagination_secret_key")


def encode_cursor(scheme_id: str, similarity_score: float, session_id: str) -> str:
    """
    Encode a cursor token from the last scheme ID and similarity score.

    Args:
        scheme_id: The scheme ID of the last item in the current page
        similarity_score: The similarity score of the last item
        session_id: The session ID to maintain across pagination requests

    Returns:
        A base64-encoded cursor token
    """
    # Create cursor data
    cursor_data = {"scheme_id": scheme_id, "similarity_score": similarity_score, "session_id": session_id}

    # Convert to JSON
    cursor_json = json.dumps(cursor_data)

    # Create signature for verification
    signature = hmac.new(CURSOR_SECRET.encode(), cursor_json.encode(), hashlib.sha256).hexdigest()

    # Combine cursor data and signature
    token_data = {"data": cursor_data, "signature": signature}

    # Encode as base64
    token_json = json.dumps(token_data)
    token_bytes = token_json.encode()
    base64_token = base64.urlsafe_b64encode(token_bytes).decode()

    return base64_token


def decode_cursor(cursor_token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a cursor token and verify its signature.

    Args:
        cursor_token: The base64-encoded cursor token

    Returns:
        The decoded cursor data or None if invalid
    """
    try:
        # Decode base64
        token_bytes = base64.urlsafe_b64decode(cursor_token)
        token_json = token_bytes.decode()
        token_data = json.loads(token_json)

        # Extract data and signature
        cursor_data = token_data.get("data")
        received_signature = token_data.get("signature")

        if not cursor_data or not received_signature:
            logger.warning("Invalid cursor format: missing data or signature")
            return None

        # Verify signature
        cursor_json = json.dumps(cursor_data)
        expected_signature = hmac.new(CURSOR_SECRET.encode(), cursor_json.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(received_signature, expected_signature):
            logger.warning("Invalid cursor signature")
            return None

        return cursor_data
    except Exception as e:
        # Any decoding error means the token is invalid
        logger.error(f"Error decoding cursor: {str(e)}")
        return None


def get_paginated_results(
    results: list, limit: int = 20, cursor: Optional[str] = None, session_id: Optional[str] = None
) -> Tuple[list, Optional[str], bool, int]:
    """
    Get paginated results based on a cursor.

    Args:
        results: The complete list of search results
        limit: The number of results to return per page
        cursor: The cursor token for the current page
        session_id: The session ID to maintain across pagination requests

    Returns:
        Tuple containing:
        - The paginated results
        - The next cursor token (or None if no more results)
        - A boolean indicating if more results exist
        - Total count of all results
    """
    total_count = len(results)

    # If no results, return empty page
    if total_count == 0:
        return [], None, False, 0

    # Get start index from cursor
    start_index = 0
    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            # Store session_id from cursor if not explicitly provided
            if session_id is None and "session_id" in cursor_data:
                session_id = cursor_data.get("session_id")

            # Find the index of the item after the cursor
            cursor_scheme_id = cursor_data.get("scheme_id")
            cursor_similarity = cursor_data.get("similarity_score")

            if cursor_scheme_id is None or cursor_similarity is None:
                logger.warning("Invalid cursor data: missing scheme_id or similarity_score")
            else:
                # Find the first item with lower similarity than the cursor
                # or the same similarity but different ID
                for i, item in enumerate(results):
                    # Check if required keys are in the item
                    if "combined_scores" not in item:
                        logger.warning(f"Missing 'combined_scores' key in search result item at index {i}")
                        continue

                    if "scheme_id" not in item:
                        logger.warning(f"Missing 'scheme_id' key in search result item at index {i}")
                        continue

                    if item["combined_scores"] < cursor_similarity or (
                        item["combined_scores"] == cursor_similarity and item["scheme_id"] > cursor_scheme_id
                    ):
                        start_index = i
                        break

    # Get results for this page
    end_index = min(start_index + limit, total_count)
    page_results = results[start_index:end_index]

    # Check if there are more results
    has_more = end_index < total_count

    # Create next cursor if there are more results
    next_cursor = None
    if has_more and page_results:
        last_item = page_results[-1]

        # Check that the required keys exist
        if "scheme_id" not in last_item:
            logger.error(f"Missing 'scheme_id' key in last result item: {last_item}")
            # Use fallback value
            scheme_id = last_item.get("id", "unknown")
        else:
            scheme_id = last_item["scheme_id"]

        if "combined_scores" not in last_item:
            logger.error(f"Missing 'combined_scores' key in last result item: {last_item}")
            # Use fallback value
            similarity = 0.0
        else:
            similarity = last_item["combined_scores"]

        next_cursor = encode_cursor(scheme_id, similarity, session_id)

    return page_results, next_cursor, has_more, total_count
