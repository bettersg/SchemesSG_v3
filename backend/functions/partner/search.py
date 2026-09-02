"""Partner search handler.

Imported lazily by ``partner/api.py`` — only inside the search branch — because
importing this module pulls in the embeddings/ranking stack at module scope. A list
or detail request must never pay that import cost.

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

from search.retriever import SearchModel
from utils.pagination import get_paginated_results, is_valid_cursor
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES

from .serializers import CURSOR_ERROR_MESSAGE, PartnerRequestError, clamp_limit, to_public_scheme


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
    # Checked before the ranking run below, so a bad cursor does not cost a full
    # embeddings pass. `get_paginated_results` would otherwise ignore it and serve
    # page one with a 200 — see `is_valid_cursor` for why the check is a payload
    # check and not only a signature check.
    if cursor is not None and not is_valid_cursor(cursor):
        raise PartnerRequestError(CURSOR_ERROR_MESSAGE)

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
