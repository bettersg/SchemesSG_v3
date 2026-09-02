"""Partner search handler.

Imported lazily by ``partner/api.py`` — only inside the search branch — because
importing this module pulls in the embeddings/ranking stack at module scope. A list
or detail request must never pay that import cost.

``SearchModel`` is called directly rather than through ``QueryHandler`` because the
handler's ``aggregate_and_rank_results`` call passes ``top_k`` where the signature
expects ``threshold``.
"""

from typing import Any

from search.retriever import SearchModel
from utils.pagination import get_paginated_results
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES

from .serializers import PartnerRequestError, clamp_limit, to_public_scheme


DEFAULT_LIMIT = 20


def handle_search(firebase_manager: Any, body: dict[str, Any]) -> dict[str, Any]:
    """Run a partner search and return the paginated public response.

    Args:
        firebase_manager: FirebaseManager providing Firestore access.
        body: Parsed JSON request body with ``query`` and optional ``limit`` / ``cursor``.

    Returns:
        ``{"data": [...], "next_cursor": ..., "has_more": ..., "total_count": ...}``

    Raises:
        PartnerRequestError: If ``query`` is missing or empty, or ``limit`` is not
            an integer.
    """
    query = str(body.get("query") or "").strip()
    if not query:
        raise PartnerRequestError("'query' is required and must be a non-empty string")

    limit = clamp_limit(body.get("limit"), default=DEFAULT_LIMIT)
    cursor = body.get("cursor") or None

    ranked = SearchModel(firebase_manager).aggregate_and_rank_results(query)
    records = [] if ranked.empty else ranked.to_dict(orient="records")

    # Stricter than any existing read path: exclude retired *and* inactive.
    listed = [record for record in records if record.get("status") not in NON_SEARCHABLE_STATUSES]

    page, next_cursor, has_more, total_count = get_paginated_results(listed, limit=limit, cursor=cursor)

    return {
        "data": [to_public_scheme(record.get("scheme_id"), record) for record in page],
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": total_count,
    }
