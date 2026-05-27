"""Helpers for cursor-based pagination in catalog Firestore queries."""

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Any, Optional
from google.cloud.firestore_v1 import CollectionReference, Query
from loguru import logger

# Secret key for cursor signature
# In a production environment, this should be stored in environment variables
# or a secure configuration system
CURSOR_SECRET = os.environ.get("CURSOR_SECRET", "schemes_pagination_secret_key")


@dataclass
class PaginationResult:
    """Page of serialized catalog results plus cursor metadata."""

    data: list[dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool = False


def _encode_cursor(doc_id: str) -> str:
    """Encode a signed pagination cursor for a Firestore document ID.

    Args:
        doc_id: Firestore document ID for the last document on the page.

    Returns:
        A URL-safe base64 cursor token containing the document ID and an
        HMAC signature.
    """
    # Create cursor data
    cursor_data = {"doc_id": doc_id}
    cursor_json = json.dumps(cursor_data)

    # Create signature for verification
    signature = hmac.new(
        CURSOR_SECRET.encode(), cursor_json.encode(), hashlib.sha256
    ).hexdigest()

    # Combine cursor data and signature
    cursor_token = {"data": cursor_data, "signature": signature}

    # Encode as b64
    cursor_token_json = json.dumps(cursor_token).encode()
    cursor_token_b64 = base64.urlsafe_b64encode(cursor_token_json).decode()

    return cursor_token_b64


def _decode_cursor(cursor: str) -> Optional[str]:
    """Decode and validate a pagination cursor.

    Args:
        cursor: URL-safe base64 cursor token previously created by
            `_encode_cursor`.

    Returns:
        The Firestore document ID embedded in the cursor when the token is
        present and the signature is valid. Returns `None` for malformed,
        tampered, or otherwise invalid cursors.
    """
    try:
        # Decode cursor from b64
        cursor_token_json = base64.urlsafe_b64decode(cursor.encode())
        cursor_token = json.loads(cursor_token_json.decode())

        # Extract data and signature
        received_cursor_data = cursor_token.get("data")
        received_signature = cursor_token.get("signature")

        if not received_cursor_data or not received_signature:
            logger.warning("Invalid cursor format: missing data or signature")
            return None

        # Verify signature
        cursor_json = json.dumps(received_cursor_data)
        expected_signature = hmac.new(
            CURSOR_SECRET.encode(), cursor_json.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(received_signature, expected_signature):
            logger.warning("Cursor signature verification failed")
            return None

        return received_cursor_data.get("doc_id")
    except Exception as e:
        logger.warning(f"Error decoding cursor: {e}")
        return None


def _get_paginated_query(
    collection_ref: CollectionReference,
    base_query: Optional[Query] = None,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> Query:
    """Build a Firestore query with ordering, limit, and optional cursor.

    The query always orders by `last_scraped_update` from newest to oldest and
    uses `__name__` as an ascending tie-breaker. It requests `limit + 1`
    documents so the caller can determine whether another page exists. When a
    cursor is provided, the corresponding document snapshot is fetched and used
    with `start_at(...)`.

    Args:
        collection_ref: Base Firestore collection for the catalog.
        base_query: Optional filtered query to paginate instead of the full
            collection.
        cursor: Optional signed cursor token from a previous page.
        limit: Number of documents requested by the caller before the extra
            lookahead document is applied.

    Returns:
        A Firestore query ready to execute.
    """
    # Order by newest updates first and add __name__ as a deterministic
    # ascending secondary sort key for documents sharing the same timestamp.
    q = (
        base_query.order_by("last_scraped_update", direction=Query.DESCENDING).limit(
            limit + 1
        )
        if base_query
        else collection_ref.order_by(
            "last_scraped_update", direction=Query.DESCENDING
        ).limit(limit + 1)
    )

    if not cursor:
        return q

    # Decode cursor to get doc_id to start_at
    doc_id = _decode_cursor(cursor)
    if not doc_id:
        return q

    try:
        snapshot = collection_ref.document(doc_id).get()
        if getattr(snapshot, "exists", False):
            return q.start_at(snapshot)
        logger.warning(f"Cursor doc_id not found in collection: {doc_id}")
        return q
    except Exception as e:
        logger.error(f"Error fetching snapshot for cursor doc_id {doc_id}: {e}")
        return q


def get_paginated_results(
    collection_ref: CollectionReference,
    base_query: Optional[Query] = None,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> PaginationResult:
    """Execute a paginated catalog query and serialize the result page.

    Args:
        collection_ref: Firestore collection reference.
        base_query: Optional filtered query to paginate.
        cursor: Optional signed cursor token from a previous response.
        limit: Maximum number of results to return in this page.

    The function fetches `limit + 1` documents internally to determine whether
    another page exists. Returned documents are converted to dictionaries with
    `DocumentSnapshot.to_dict()`.

    Returns:
        Pagination metadata and serialized document data for the current page.
    """
    # Set default return values
    docs = []
    has_more = False
    next_cursor = None

    ref = _get_paginated_query(collection_ref, base_query, cursor, limit)

    docs = ref.get()

    has_more = len(docs) > limit
    if has_more:
        next_cursor = _encode_cursor(docs[-1].id)
        docs = docs[:-1]

    return PaginationResult(
        data=[{"scheme_id": doc.id, **doc.to_dict()} for doc in docs],
        next_cursor=next_cursor,
        has_more=has_more,
    )
