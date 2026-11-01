"""
Handler for catalog endpoint

URL for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?agency=<agency>
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?area=<area>
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?category=<category>
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?category=<a>&category=<b>&area=<area>
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Sequence

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from google.cloud.firestore_v1 import FieldFilter
from loguru import logger
from new_scheme.constants import LEGACY_CATEGORY_TERMS, SCHEME_CATEGORY_MAPPING
from utils.catalog_filtering import (
    MAX_DISJUNCTION_VALUES,
    CatalogFilters,
    get_filtered_results,
    known_agencies,
    resolve_agencies,
)
from utils.catalog_pagination import CATALOG_FIELDS, PaginationResult, _count_total, get_paginated_results
from utils.cors_config import get_cors_headers, handle_cors_preflight
from utils.json_utils import safe_json_dumps
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES
from werkzeug.datastructures import MultiDict


DEFAULT_LIMIT = 10


@dataclass(frozen=True)
class CatalogFilterSpec:
    """Describes how a supported catalog query param maps to Firestore."""

    firestore_field: str
    operator: str
    normalize: Callable[[str], str | list[str]]


@dataclass(kw_only=True)
class CatalogRequestParams:
    """Parsed catalog request parameters: normalized values per active filter."""

    limit: int = DEFAULT_LIMIT
    cursor: str | None = None
    filters: dict[str, list[str]] = field(default_factory=dict)


# v2 terms first, then pre-v2 terms so schemes that still carry the old vocabulary stay reachable until migrated
_CATEGORY_LOOKUP = {
    cat.lower(): [*types, *LEGACY_CATEGORY_TERMS.get(cat, [])] for cat, types in SCHEME_CATEGORY_MAPPING.items()
}


def _expand_category(value: str) -> list[str]:
    types = _CATEGORY_LOOKUP.get(value.lower())
    if types is None:
        raise ValueError(f"Unknown category: '{value}'")
    return types


def _filter_scheme_types_for_category(results: PaginationResult, category_scheme_types: list[str]) -> PaginationResult:
    """Trim scheme_type values in category catalog responses to the matched category."""

    category_scheme_type_set = set(category_scheme_types)
    filtered_data = []

    for item in results.data:
        scheme_type = item.get("scheme_type")
        if not isinstance(scheme_type, list):
            filtered_data.append(item)
            continue

        filtered_data.append(
            {
                **item,
                "scheme_type": [value for value in scheme_type if value in category_scheme_type_set],
            }
        )

    return PaginationResult(
        data=filtered_data,
        next_cursor=results.next_cursor,
        has_more=results.has_more,
        total_count=results.total_count,
    )


# The catalog lists what search lists: an inactive scheme's official link is dead,
# so browsing must not surface it either.
_CATALOG_EXCLUDED_STATUSES: frozenset[str] = NON_SEARCHABLE_STATUSES


def _keep_listed_schemes(
    results: PaginationResult,
    exclude_statuses: frozenset[str] = _CATALOG_EXCLUDED_STATUSES,
) -> PaginationResult:
    """Remove schemes whose lifecycle status must not appear in a listing."""
    return PaginationResult(
        data=[item for item in results.data if item.get("status") not in exclude_statuses],
        next_cursor=results.next_cursor,
        has_more=results.has_more,
        total_count=results.total_count,
    )


def _count_excluded_schemes(
    collection_ref,
    base_query: Any = None,
    exclude_statuses: frozenset[str] = _CATALOG_EXCLUDED_STATUSES,
) -> int | None:
    """Count documents matching the unpaginated query whose status is excluded.

    One ``==`` count per status rather than a single ``in``: it keeps the query
    shape the catalog has always issued, so no new composite index is needed.
    """
    source = base_query if base_query is not None else collection_ref
    counts = [_count_total(collection_ref, source.where("status", "==", status)) for status in exclude_statuses]
    return None if None in counts else sum(counts)


def _get_listed_paginated_results(
    collection_ref,
    *,
    base_query: Any = None,
    cursor: str | None = None,
    limit: int = DEFAULT_LIMIT,
    exclude_statuses: frozenset[str] = _CATALOG_EXCLUDED_STATUSES,
    fields: Sequence[str] = CATALOG_FIELDS,
) -> PaginationResult:
    """Fill a page to ``limit``, skipping documents with an excluded status.

    The refill loop and the ``total_count`` adjustment both honour
    ``exclude_statuses``, so pages stay full and the count matches what is
    actually returned.
    """
    data = []
    current_cursor = cursor
    seen_cursors = {cursor} if cursor else set()
    last_result = PaginationResult(data=[])
    repeated_cursor = False

    while len(data) < limit:
        last_result = get_paginated_results(
            collection_ref=collection_ref,
            base_query=base_query,
            cursor=current_cursor,
            limit=limit - len(data),
            fields=fields,
        )
        data.extend(_keep_listed_schemes(last_result, exclude_statuses).data)

        next_cursor = last_result.next_cursor
        if not last_result.has_more or not next_cursor:
            break
        if next_cursor in seen_cursors:
            repeated_cursor = True
            break
        seen_cursors.add(next_cursor)
        current_cursor = next_cursor

    excluded_count = _count_excluded_schemes(collection_ref, base_query, exclude_statuses)
    listed_total = (
        last_result.total_count - excluded_count
        if last_result.total_count is not None and excluded_count is not None
        else None
    )

    return PaginationResult(
        data=data[:limit],
        next_cursor=None if repeated_cursor else last_result.next_cursor,
        has_more=False if repeated_cursor else last_result.has_more,
        total_count=listed_total,
    )


FILTER_SPECS = {
    # Kept as given: list_schemes resolves it against the stored spellings.
    "agency": CatalogFilterSpec(
        firestore_field="agency",
        operator="in",
        normalize=lambda value: value,
    ),
    "area": CatalogFilterSpec(
        firestore_field="planning_area",
        operator="array_contains",
        normalize=lambda value: value.upper(),
    ),
    "category": CatalogFilterSpec(
        firestore_field="scheme_type",
        operator="array_contains_any",
        normalize=_expand_category,
    ),
}
ALLOWED_QUERY_PARAMS = set(FILTER_SPECS) | {"limit", "cursor", "is_warmup", "sort"}


def normalize_filter_values(name: str, raw_values: Sequence[str]) -> list[str]:
    """Normalize every value of one filter; a category expands to its scheme types.

    Raises:
        ValueError: If a value is not valid for the filter (e.g. an unknown category).
    """
    normalized: list[str] = []
    for raw in raw_values:
        value = FILTER_SPECS[name].normalize(raw)
        normalized.extend(value if isinstance(value, list) else [value])
    return list(dict.fromkeys(normalized))


def build_catalog_filters(
    collection_ref, values: dict[str, list[str]], updated_since: datetime | None = None
) -> CatalogFilters:
    """Turn normalized request values into filters, resolving agency spellings against the stored names."""
    agency = values.get("agency", [])
    return CatalogFilters(
        agency=tuple(resolve_agencies(agency, known_agencies(collection_ref))) if agency else (),
        area=tuple(values.get("area", [])),
        scheme_types=tuple(values.get("category", [])),
        updated_since=updated_since,
    )


def list_schemes(
    collection_ref,
    filters: CatalogFilters,
    *,
    cursor: str | None = None,
    limit: int = DEFAULT_LIMIT,
    exclude_statuses: frozenset[str] = _CATALOG_EXCLUDED_STATUSES,
    fields: Sequence[str] = CATALOG_FIELDS,
) -> PaginationResult:
    """List schemes for the catalog and the partner API.

    No filter, or a single agency or category filter, pages in Firestore. Anything
    else (several filters, area, updated_since) fetches one filter's candidates from
    Firestore and applies the rest in memory: see ``utils.catalog_filtering``.
    """
    active = filters.active
    single_db_filter = None
    if active == ["agency"] and len(filters.agency) <= MAX_DISJUNCTION_VALUES:
        single_db_filter = FieldFilter("agency", "in", list(filters.agency))
    elif active == ["scheme_types"] and len(filters.scheme_types) <= MAX_DISJUNCTION_VALUES:
        single_db_filter = FieldFilter("scheme_type", "array_contains_any", list(filters.scheme_types))

    if not active or single_db_filter is not None:
        return _get_listed_paginated_results(
            collection_ref=collection_ref,
            base_query=collection_ref.where(filter=single_db_filter) if single_db_filter is not None else None,
            cursor=cursor,
            limit=limit,
            exclude_statuses=exclude_statuses,
            fields=fields,
        )

    return get_filtered_results(
        collection_ref,
        filters,
        fields=fields,
        cursor=cursor,
        limit=limit,
        exclude_statuses=exclude_statuses,
    )


def create_firebase_manager() -> FirebaseManager:
    """Factory function to create a FirebaseManager instance."""

    return FirebaseManager()


def _supported_catalog_query_message() -> str:
    """Return the standard validation error for supported catalog query shapes."""

    supported_queries = [
        "/catalog",
        *[f"/catalog?{name}=<{name}>" for name in FILTER_SPECS],
    ]
    return (
        f"Error parsing query parameters; only {', '.join(supported_queries)} are supported. "
        "Filters combine, and each may repeat to match any of several values."
    )


@https_fn.on_request(region="asia-southeast1", memory=options.MemoryOption.GB_1)
def catalog(req: https_fn.Request) -> https_fn.Response:
    """
    Handler for catalog endpoint

    Args:
        req (https_fn.Request): request sent from client

    Returns:
        https_fn.Response: response sent to client
    """
    # Handle CORS preflight request
    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    # Get standard CORS headers for all other requests
    headers = get_cors_headers(req)

    if not req.method == "GET":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only GET is supported"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    # Check if this is a warmup request from the query parameters
    is_warmup = req.args.get("is_warmup", "false").lower() == "true"

    if is_warmup:
        return https_fn.Response(
            response=json.dumps({"message": "Warmup request received"}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    # Catalog data is intentionally public. It contains the same scheme
    # information shown to all visitors and is required during static builds.
    firebase_manager = create_firebase_manager()

    try:
        query_params = _parse_query_params(req.args)
    except ValueError as e:
        logger.exception("Error parsing query parameters", e)
        return https_fn.Response(
            response=json.dumps({"error": _supported_catalog_query_message()}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    try:
        results = _handle_catalog_request(firebase_manager, query_params)
    except Exception as e:
        logger.exception("Unable to fetch scheme from firestore", e)
        return https_fn.Response(
            response=json.dumps({"error": "Internal server error, unable to fetch scheme from firestore"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )

    if results.data is None or len(results.data) == 0:
        return https_fn.Response(
            response=json.dumps({"error": "No scheme found"}),
            status=404,
            mimetype="application/json",
            headers=headers,
        )

    return https_fn.Response(
        response=safe_json_dumps(asdict(results)),
        status=200,
        mimetype="application/json",
        headers=headers,
    )


def _parse_query_params(query_params: MultiDict[str, str]) -> CatalogRequestParams:
    """
    Parse request query parameters into CatalogRequestParams.

    Supported:
      - /catalog
      - /catalog?agency=<name>
      - /catalog?area=<name>
      - /catalog?category=<name>
      - any combination, each repeatable: /catalog?category=<a>&category=<b>&area=<name>
        (OR within a filter, AND across filters)

    Raises:
        ValueError: If unsupported query parameters or invalid values are provided.
    """

    # Validate unknown query parameters
    unknown_params = set(query_params.keys()) - ALLOWED_QUERY_PARAMS
    if unknown_params:
        raise ValueError(f"Unsupported query parameter(s): {', '.join(sorted(unknown_params))}")

    # Retrieve limit and cursor from query parameters
    limit = int(query_params.get("limit", DEFAULT_LIMIT))
    cursor = query_params.get("cursor", "")

    filters: dict[str, list[str]] = {}
    for name in FILTER_SPECS:
        if name not in query_params:
            continue
        raw_values = [value.strip() for value in query_params.getlist(name) if value.strip()]
        if not raw_values:
            raise ValueError(f"Invalid query; '{name}' must be a non-empty value")
        filters[name] = normalize_filter_values(name, raw_values)

    return CatalogRequestParams(filters=filters, limit=limit, cursor=cursor)


def _handle_catalog_request(
    firebase_manager: FirebaseManager,
    query_params: CatalogRequestParams,
) -> PaginationResult:
    """Retrieve catalog entries with optional filter-based pagination.

    Args:
        firebase_manager: Firebase manager providing Firestore access.
        query_params: Parsed catalog parameters, including any active filters.

    Returns:
        PaginationResult:
            data: Documents for the current page.
            next_cursor: Cursor for the next page, or None if exhausted.
            has_more: Whether more results exist.
    """
    col = firebase_manager.firestore_client.collection("schemes")
    filters = build_catalog_filters(col, query_params.filters)

    results = list_schemes(col, filters, cursor=query_params.cursor, limit=query_params.limit)

    if filters.scheme_types:
        return _filter_scheme_types_for_category(results, list(filters.scheme_types))

    return results
