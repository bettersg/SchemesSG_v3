"""Partner API — a single Firebase function serving the versioned partner surface.

    GET   /v1/schemes              list + filter
    GET   /v1/schemes/{scheme_id}  detail
    POST  /v1/schemes/search       semantic search

One function rather than three because the version belongs in the path, not in a
function name: a Firebase function's name is the first path segment, so it forms
the *service root* and everything after it arrives as ``req.path`` to route.

Local testing:
    http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/partner_api/v1/schemes

Warmup: kept warm by ``keep_endpoints_warm`` like the rest of the API. The
``is_warmup`` short-circuit sits *after* key verification and *before* the rate
limiter, so it is not an unauthenticated path — the warmer holds a real key issued
to the ``warmup`` consumer — and the 4-minutely ping neither spends a partner's
budget nor writes a counter document. Requires ``PARTNER_WARMUP_API_KEY``; see
docs/partner-api-runbook.md.

Deliberately absent:

* **No CORS.** ``utils/cors_config.ALLOWED_ORIGINS`` is a browser-``Origin``
  allowlist, and CORS is enforced by browsers, not by servers — a partner's backend
  ignores it entirely. Omitting it is the security control: the only way a partner
  could use this from browser JavaScript is by shipping their secret key to every
  end user, so the absent headers make that mistake fail in development instead of
  leaking the key in production. A partner needing browser access should proxy
  through their own backend. **Do not add partner domains to ALLOWED_ORIGINS.**
"""

from typing import Any

from fb_manager.firebaseManager import FirebaseManager
from firebase_functions import https_fn, options
from loguru import logger
from schemes.catalog import DEFAULT_LIMIT, FILTER_SPECS, InvalidFilterValue, fetch_listed_page
from utils.json_utils import safe_json_dumps
from utils.partner_auth import AuthError, check_and_increment_rate_limit, verify_partner_key
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES, RETIRED_STATUS

from .routing import Route, RouteError, resolve_route
from .serializers import (
    PartnerRequestError,
    clamp_limit,
    error_body,
    to_public_scheme,
)


SCHEMES_COLLECTION = "schemes"

# Partner list params: the shared catalog filters plus pagination, and `is_warmup`
# so the warmer's ping isn't rejected as an unknown parameter. Notably no `sort`,
# unlike the frontend's /catalog.
LIST_QUERY_PARAMS = set(FILTER_SPECS) | {"limit", "cursor", "is_warmup"}


def create_firebase_manager() -> FirebaseManager:
    """Factory function to create a FirebaseManager instance."""
    return FirebaseManager()


@https_fn.on_request(
    region="asia-southeast1",
    # 2GB because the search branch loads the embeddings/ranking stack.
    #
    # This module keeps that stack out of its own import graph (see the lazy import
    # in _dispatch, asserted by test_partner_handlers.py). Be aware that today it
    # buys nothing at runtime: main.py imports agent.handler at module scope, which
    # imports search.retriever, so every function in this deployment already pays
    # the load. The lazy import is the half we control, and it starts paying off
    # the moment agent.handler defers its own import.
    memory=options.MemoryOption.GB_2,
)
def partner_api(req: https_fn.Request) -> https_fn.Response:
    """Handler for the partner API.

    Args:
        req (https_fn.Request): request sent from the partner.

    Returns:
        https_fn.Response: response sent to the partner.
    """
    # Auth and throttling talk to Firestore, so they can raise. Wrapped so a
    # backend blip still answers in the documented error envelope, not a bare 500.
    try:
        db = create_firebase_manager().firestore_client

        identity = verify_partner_key(req, db)
        if isinstance(identity, AuthError):
            # No consumer was identified, so there is no budget to report. Rate-limit
            # headers are deliberately absent here rather than guessed at.
            return _error(identity.code, identity.message, identity.status)

        # Warmup runs *after* auth, matching every other endpoint in this codebase
        # (see schemes/catalog.py), so this is not an unauthenticated code path —
        # keep_endpoints_warm holds a real key for the `warmup` consumer. Placed
        # before the rate limiter so the 4-minutely ping neither spends a budget nor
        # writes a counter document. Still reports the budget it did not spend.
        if req.args.get("is_warmup", "").lower() == "true":
            return _json(
                {"message": "Warmup request received"},
                headers=_limit_headers(identity.rate_limit_per_min, identity.rate_limit_per_min),
            )

        allowed, remaining = check_and_increment_rate_limit(
            db, identity.consumer, identity.rate_limit_per_min
        )
    except Exception:  # noqa: BLE001 - partner-facing 5xx must not leak internals
        logger.exception("partner_api auth/rate-limit failed")
        return _error("internal_error", "Internal server error", 500)

    rate_limit = identity.rate_limit_per_min
    rate_headers = _limit_headers(remaining, rate_limit)
    if not allowed:
        return _error(
            "rate_limited",
            f"Rate limit of {rate_limit} requests/minute exceeded",
            429,
            headers={**rate_headers, "Retry-After": "60"},
        )

    route = resolve_route(req.method, req.path)
    if isinstance(route, RouteError):
        return _error(route.code, route.message, route.status, headers=rate_headers)

    try:
        return _dispatch(route, req, db, rate_headers)
    except PartnerRequestError as exc:
        # Only messages authored in this package reach a partner. A bare
        # `except ValueError` here would also echo messages raised inside
        # Firestore, pandas or the shared catalog helpers.
        return _error("invalid_request", exc.client_message, 400, headers=rate_headers)
    except Exception:  # noqa: BLE001 - partner-facing 5xx must not leak internals
        logger.exception(f"partner_api failed for consumer={identity.consumer} path={req.path}")
        return _error("internal_error", "Internal server error", 500, headers=rate_headers)


def _dispatch(route: Route, req: https_fn.Request, db: Any, headers: dict[str, str]) -> https_fn.Response:
    """Route a verified request to its handler."""
    if route.kind == "list":
        return _json(_handle_list(db, req.args), headers=headers)

    if route.kind == "detail":
        body, status = _handle_detail(db, route.scheme_id)
        return _json(body, status=status, headers=headers)

    # Validated before the import below, so a malformed body is rejected without
    # paying for the embeddings stack. `get_json` happily returns a list, string
    # or number for valid JSON that isn't an object, and handle_search would then
    # blow up on .get() as a 500.
    payload = req.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        raise PartnerRequestError("Request body must be a JSON object")

    # Lazy import: keeps the embeddings/ranking stack out of list and detail.
    from .search import handle_search

    return _json(handle_search(create_firebase_manager(), payload), headers=headers)


def _handle_list(db: Any, args: Any) -> dict[str, Any]:
    """List schemes with optional single-filter pagination."""
    unknown = set(args.keys()) - LIST_QUERY_PARAMS
    if unknown:
        raise PartnerRequestError(f"Unsupported query parameter(s): {', '.join(sorted(unknown))}")

    selected = [name for name in FILTER_SPECS if args.get(name)]
    if len(selected) > 1:
        raise PartnerRequestError(f"{', '.join(repr(name) for name in selected)} cannot be used together")

    filter_name = selected[0] if selected else None
    raw_value = args.get(filter_name) if filter_name else None

    # Partners never see retired *or* inactive. Passing the set down rather than
    # filtering the returned page keeps pages full and total_count honest.
    try:
        results = fetch_listed_page(
            db.collection(SCHEMES_COLLECTION),
            filter_name=filter_name,
            filter_raw_value=raw_value,
            cursor=args.get("cursor") or None,
            limit=clamp_limit(args.get("limit"), default=DEFAULT_LIMIT),
            exclude_statuses=NON_SEARCHABLE_STATUSES,
        )
    except InvalidFilterValue as exc:
        # Precisely this exception, not bare ValueError: a ValueError from inside
        # pagination must stay a logged 500 rather than have its internal message
        # restated to a partner. The message here is ours, not the catalog's.
        raise PartnerRequestError(f"Invalid value for {filter_name!r}: {str(raw_value)!r}") from exc

    return {
        "data": [to_public_scheme(item.get("scheme_id"), item) for item in results.data],
        "next_cursor": results.next_cursor,
        "has_more": results.has_more,
        "total_count": results.total_count,
    }


def _handle_detail(db: Any, scheme_id: str) -> tuple[dict[str, Any], int]:
    """Fetch one scheme by ID, signalling merge targets for retired schemes."""
    doc = db.collection(SCHEMES_COLLECTION).document(scheme_id).get()
    if not doc.exists:
        return error_body("not_found", "Scheme with provided id does not exist"), 404

    data = doc.to_dict() or {}
    status = data.get("status")

    if status in NON_SEARCHABLE_STATUSES:
        merged_into = data.get("merged_into")
        if status == RETIRED_STATUS and merged_into:
            # A bare 404 would leave the partner holding a dead id with no way to
            # learn it became a different one.
            return (
                error_body(
                    "scheme_retired",
                    "Scheme was retired and merged into another scheme",
                    merged_into=merged_into,
                ),
                404,
            )
        return error_body("not_found", "Scheme with provided id does not exist"), 404

    return {"data": to_public_scheme(doc.id, data)}, 200


def _limit_headers(remaining: int, limit: int) -> dict[str, str]:
    return {"X-RateLimit-Remaining": str(remaining), "X-RateLimit-Limit": str(limit)}


def _json(body: dict[str, Any], status: int = 200, headers: dict[str, str] | None = None) -> https_fn.Response:
    return https_fn.Response(
        response=safe_json_dumps(body),
        status=status,
        mimetype="application/json",
        headers=headers or {},
    )


def _error(code: str, message: str, status: int, headers: dict[str, str] | None = None) -> https_fn.Response:
    return _json(error_body(code, message), status=status, headers=headers)
