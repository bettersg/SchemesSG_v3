"""Path routing for the partner API.

Kept as a pure function so the whole URL contract is testable without Firebase.
The version lives in the path (``/v1/schemes``), not in the function name — the
Firebase function name is part of the service root, so it carries no version.
"""

from dataclasses import dataclass
from typing import Literal


API_VERSION = "v1"
RESOURCE = "schemes"

# A leaf that is an operation, not a scheme ID. Without reserving it, a scheme whose
# document ID is literally "search" would shadow the search route.
SEARCH_LEAF = "search"

RouteKind = Literal["list", "detail", "search"]


@dataclass(frozen=True)
class Route:
    """A resolved partner API operation."""

    kind: RouteKind
    scheme_id: str | None = None


@dataclass(frozen=True)
class RouteError:
    """A routing failure, already carrying its HTTP status."""

    code: str
    message: str
    status: int


def resolve_route(method: str, path: str) -> Route | RouteError:
    """Resolve an HTTP method and path into a partner API operation.

    Args:
        method: HTTP method of the request.
        path: Request path *after* the Firebase function name, e.g. ``/v1/schemes``.

    Returns:
        A ``Route`` when the request addresses a real operation, otherwise a
        ``RouteError``. An unknown or absent version is always an error: we never
        fall through to an implicit v1.
    """
    segments = [segment for segment in path.split("/") if segment]

    if not segments or segments[0] != API_VERSION:
        return RouteError(
            code="unsupported_version",
            message=f"Unsupported API version; only /{API_VERSION} is available",
            status=404,
        )

    if len(segments) < 2 or segments[1] != RESOURCE:
        return RouteError(
            code="not_found",
            message=f"Unknown resource; only /{API_VERSION}/{RESOURCE} is available",
            status=404,
        )

    tail = segments[2:]

    if not tail:
        if method != "GET":
            return _method_not_allowed(method, "GET")
        return Route(kind="list")

    if len(tail) > 1:
        return RouteError(code="not_found", message="Unknown path", status=404)

    leaf = tail[0]

    if leaf == SEARCH_LEAF:
        if method != "POST":
            return _method_not_allowed(method, "POST")
        return Route(kind="search")

    if method != "GET":
        return _method_not_allowed(method, "GET")
    return Route(kind="detail", scheme_id=leaf)


def _method_not_allowed(method: str, expected: str) -> RouteError:
    return RouteError(
        code="method_not_allowed",
        message=f"{method} is not supported here; use {expected}",
        status=405,
    )
