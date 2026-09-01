"""Partner search handler.

Imported lazily by ``partner/api.py`` — only inside the search branch — because
this module pulls in the embeddings/ranking stack. A list or detail request must
never pay that import cost.

Built on ``search.retriever.SearchModel`` rather than ``ml_logic``: the ml_logic
path still calls the removed ``BM25Retriever.get_relevant_documents()`` and 500s
on real queries, while ``search/`` uses the current ``.invoke()`` API and already
serves the chat agent in production.

``SearchModel`` is called directly rather than through ``QueryHandler`` for two
reasons: ``QueryHandler.predict_paginated`` persists every query into the
``userQuery`` collection, which is the site's own analytics and should not be
polluted with partner traffic; and its ``aggregate_and_rank_results`` call passes
``top_k`` where the signature expects ``threshold``.
"""

from typing import Any

from utils.pagination import get_paginated_results
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES

from .serializers import to_public_scheme


DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def handle_search(firebase_manager: Any, body: dict[str, Any]) -> dict[str, Any]:
    """Run a partner search and return the paginated public response.

    Args:
        firebase_manager: FirebaseManager providing Firestore access.
        body: Parsed JSON request body with ``query`` and optional ``limit`` / ``cursor``.

    Returns:
        ``{"data": [...], "next_cursor": ..., "has_more": ..., "total_count": ...}``

    Raises:
        ValueError: If ``query`` is missing, empty, or ``limit`` is not an integer.
    """
    # Imported here rather than at module scope so that importing this module is
    # cheap for callers that only want the constants.
    from search.retriever import SearchModel

    query = str(body.get("query") or "").strip()
    if not query:
        raise ValueError("'query' is required and must be a non-empty string")

    limit = _clamp_limit(body.get("limit"))
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


def _clamp_limit(raw: Any) -> int:
    """Clamp a requested page size into ``1..MAX_LIMIT``."""
    if raw is None:
        return DEFAULT_LIMIT
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise ValueError("'limit' must be an integer") from None
    return max(1, min(limit, MAX_LIMIT))
