"""
Handler for catalog endpoint

URL for local testing:
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?agency=<agency>
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?area=<area>
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/catalog?category=<category>
"""

import json
from dataclasses import asdict, dataclass
from typing import Callable

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from google.cloud.firestore_v1 import FieldFilter
from loguru import logger
from new_scheme.constants import SCHEME_CATEGORY_MAPPING
from utils.auth import verify_auth_token
from utils.catalog_pagination import PaginationResult, get_paginated_results
from utils.cors_config import get_cors_headers, handle_cors_preflight
from utils.json_utils import safe_json_dumps
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
    """Parsed catalog request parameters with an optional active filter."""

    limit: int = DEFAULT_LIMIT
    cursor: str | None = None
    filter_name: str | None = None
    filter_value: str | list[str] | None = None


_CATEGORY_LOOKUP = {cat.lower(): types for cat, types in SCHEME_CATEGORY_MAPPING.items()}


def _expand_category(value: str) -> list[str]:
    types = _CATEGORY_LOOKUP.get(value.lower())
    if types is None:
        raise ValueError(f"Unknown category: '{value}'")
    return types


FILTER_SPECS = {
    "agency": CatalogFilterSpec(
        firestore_field="agency",
        operator="==",
        normalize=lambda value: value.title(),
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


def create_firebase_manager() -> FirebaseManager:
    """Factory function to create a FirebaseManager instance."""

    return FirebaseManager()


def _supported_catalog_query_message() -> str:
    """Return the standard validation error for supported catalog query shapes."""

    supported_queries = [
        "/catalog",
        *[f"/catalog?{name}=<{name}>" for name in FILTER_SPECS],
    ]
    return f"Error parsing query parameters; only {', '.join(supported_queries)} are supported"


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

    # Verify authentication
    is_valid, auth_message = verify_auth_token(req)
    if not is_valid:
        return https_fn.Response(
            response=json.dumps({"error": f"Authentication failed: {auth_message}"}),
            status=401,
            mimetype="application/json",
            headers=headers,
        )

    firebase_manager = create_firebase_manager()

    if not req.method == "GET":
        return https_fn.Response(
            response=json.dumps(
                {"error": "Invalid request method; only GET is supported"}
            ),
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
            response=json.dumps(
                {
                    "error": "Internal server error, unable to fetch scheme from firestore"
                }
            ),
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

    Raises:
        ValueError: If unsupported query parameters are provided.
    """

    # Validate unknown query parameters
    unknown_params = set(query_params.keys()) - ALLOWED_QUERY_PARAMS
    if unknown_params:
        raise ValueError(
            f"Unsupported query parameter(s): {', '.join(sorted(unknown_params))}"
        )

    selected_filters = [name for name in FILTER_SPECS if query_params.get(name)]
    if len(selected_filters) > 1:
        raise ValueError(
            f"Invalid query; {', '.join(repr(name) for name in selected_filters)} cannot be used together"
        )

    # Retrieve limit and cursor from query parameters
    limit = int(query_params.get("limit", DEFAULT_LIMIT))
    cursor = query_params.get("cursor", "")

    if not selected_filters:
        return CatalogRequestParams(limit=limit, cursor=cursor)

    filter_name = selected_filters[0]
    raw_value = query_params.get(filter_name, "")
    if not raw_value.strip():
        raise ValueError(f"Invalid query; '{filter_name}' must be a non-empty value")

    spec = FILTER_SPECS[filter_name]
    return CatalogRequestParams(
        filter_name=filter_name,
        filter_value=spec.normalize(raw_value.strip()),
        limit=limit,
        cursor=cursor,
    )


def _handle_catalog_request(
    firebase_manager: FirebaseManager,
    query_params: CatalogRequestParams,
) -> PaginationResult:
    """Retrieve catalog entries with optional filter-based pagination.

    Args:
        firebase_manager: Firebase manager providing Firestore access.
        query_params: Parsed catalog parameters, including any active filter.

    Returns:
        PaginationResult:
            data: Documents for the current page.
            next_cursor: Cursor for the next page, or None if exhausted.
            has_more: Whether more results exist.
    """
    col = firebase_manager.firestore_client.collection("schemes")

    if not query_params.filter_name or query_params.filter_value is None:
        return get_paginated_results(
            collection_ref=col,
            cursor=query_params.cursor,
            limit=query_params.limit,
        )

    spec = FILTER_SPECS[query_params.filter_name]
    query = col.where(
        filter=FieldFilter(
            spec.firestore_field, spec.operator, query_params.filter_value
        )
    )

    return get_paginated_results(
        collection_ref=col,
        base_query=query,
        cursor=query_params.cursor,
        limit=query_params.limit,
    )
