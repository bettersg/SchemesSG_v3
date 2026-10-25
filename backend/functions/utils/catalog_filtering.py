"""Multi-filter catalog listing: one filter runs in Firestore, the rest in memory.

A single agency or category filter still pages in Firestore (see
``schemes.catalog``). This module covers what Firestore cannot do in one query:

* several filters at once. Firestore allows one ``in`` / ``array_contains_any``
  per query, and an ordered query on two fields needs a composite index per pair;
* ``planning_area``, stored as a plain string on most schemes and as a list on the
  rest, so ``array_contains`` alone misses the string ones, and in whatever case the
  approver typed, so requested areas resolve against the stored spellings;
* ``updated_since``, whose source fields carry three types from different writers
  (``Timestamp``, a ``{"_seconds", "_nanoseconds"}`` map from a 2025 import, an ISO
  string). The map-typed ``last_scraped_update`` cannot be range-queried, so those
  schemes surface through ``updated_since`` only after a status change or rescrape.

The most selective filter fetches candidates from Firestore without ``order_by``
(single-field indexes only, so nothing to deploy), the remaining filters apply in
memory, and the page is cut in memory. The catalog holds under a thousand schemes,
so the candidate set stays small.
"""

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from google.cloud.firestore_v1 import FieldFilter

from utils.catalog_pagination import PaginationResult, _decode_cursor, _encode_cursor


# Firestore caps the values in one `in` / `array_contains_any` filter.
MAX_DISJUNCTION_VALUES = 30
AGENCY_CACHE_TTL_SECONDS = 300

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_BRACKETED = re.compile(r"\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9]")


@dataclass(frozen=True)
class CatalogFilters:
    """Resolved filter values. Empty means the filter is not applied.

    ``agency`` holds stored agency names (already resolved), ``area`` upper-cased
    planning areas, ``scheme_types`` the scheme types the requested categories expand to.
    """

    agency: tuple[str, ...] = ()
    area: tuple[str, ...] = ()
    scheme_types: tuple[str, ...] = ()
    updated_since: datetime | None = None

    @property
    def active(self) -> list[str]:
        names = [name for name in ("agency", "area", "scheme_types") if getattr(self, name)]
        return [*names, "updated_since"] if self.updated_since else names


def as_datetime(value: Any) -> datetime | None:
    """Read a stored timestamp in any of the shapes older imports left behind."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, dict) and "_seconds" in value:
        return datetime.fromtimestamp(value["_seconds"] + value.get("_nanoseconds", 0) / 1e9, tz=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return as_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def updated_at(doc: dict[str, Any]) -> datetime | None:
    """Last content or status change: the later of the last scrape and the last status change."""
    stamps = [as_datetime(doc.get("last_scraped_update")), as_datetime(doc.get("status_updated_at"))]
    present = [stamp for stamp in stamps if stamp]
    return max(present) if present else None


def parse_updated_since(raw: str) -> datetime:
    """Parse an ISO 8601 date or datetime; a value without an offset is read as UTC.

    Raises:
        ValueError: If ``raw`` is not ISO 8601.
    """
    parsed = as_datetime(raw.strip())
    if parsed is None:
        raise ValueError(f"Invalid ISO 8601 value: {raw!r}")
    return parsed


def agency_key(name: str) -> str:
    """Compare agency names ignoring case, punctuation and a bracketed abbreviation.

    "TOUCH Community Services" and "Touch Community Services" match, and so do
    "Agency for Integrated Care" and "Agency for Integrated Care (AIC)".
    """
    return _NON_ALNUM.sub("", _BRACKETED.sub("", name.lower()))


def resolve_agencies(requested: Iterable[str], known: Iterable[str]) -> list[str]:
    """Map requested agency names to every stored spelling that matches them.

    A requested name with no stored match is kept as given, so the query still
    runs and returns nothing rather than silently dropping the filter.
    """
    by_key: dict[str, list[str]] = {}
    for name in known:
        if name:
            by_key.setdefault(agency_key(name), []).append(name)
    resolved: list[str] = []
    for name in requested:
        resolved.extend(by_key.get(agency_key(name), [name]))
    return list(dict.fromkeys(resolved))


def resolve_areas(requested: Iterable[str], known: Iterable[str]) -> list[str]:
    """Map upper-cased planning areas to every stored spelling that matches them, ignoring case.

    The Slack approval modal takes planning area as free text, so "Bedok" is stored
    beside "BEDOK". The requested values are kept, so an area with no stored match
    still queries and returns nothing.
    """
    wanted = set(requested)
    return list(dict.fromkeys([*requested, *(name for name in known if name.upper() in wanted)]))


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return [value] if isinstance(value, str) else []


_known_cache: dict[str, tuple[float, list[str]]] = {}


def _known_values(collection_ref: Any, field: str) -> list[str]:
    """Distinct stored values of ``field`` (list items included), cached per instance for a few minutes."""
    now = time.monotonic()
    cached = _known_cache.get(field)
    if cached is None or now - cached[0] > AGENCY_CACHE_TTL_SECONDS:
        values = {
            value
            for doc in collection_ref.select([field]).stream()
            for value in _as_list((doc.to_dict() or {}).get(field))
        }
        cached = (now, sorted(values))
        _known_cache[field] = cached
    return cached[1]


def known_agencies(collection_ref: Any) -> list[str]:
    """Distinct stored agency names, cached per instance for a few minutes."""
    return _known_values(collection_ref, "agency")


def known_planning_areas(collection_ref: Any) -> list[str]:
    """Distinct stored planning area spellings, cached per instance for a few minutes."""
    return _known_values(collection_ref, "planning_area")


def matches(doc: dict[str, Any], filters: CatalogFilters) -> bool:
    """True when the document passes every active filter (OR within a filter, AND across)."""
    if filters.agency and doc.get("agency") not in filters.agency:
        return False
    if filters.area and not {area.upper() for area in _as_list(doc.get("planning_area"))} & set(filters.area):
        return False
    if filters.scheme_types and not set(_as_list(doc.get("scheme_type"))) & set(filters.scheme_types):
        return False
    if filters.updated_since:
        stamp = updated_at(doc)
        if stamp is None or stamp < filters.updated_since:
            return False
    return True


def _chunks(values: Sequence[str]) -> list[list[str]]:
    return [list(values[i : i + MAX_DISJUNCTION_VALUES]) for i in range(0, len(values), MAX_DISJUNCTION_VALUES)]


def _candidate_filters(collection_ref: Any, filters: CatalogFilters) -> list[FieldFilter]:
    """Firestore filters for the most selective active filter; their results are unioned."""
    if filters.updated_since:
        since = filters.updated_since
        # Range filters are type-strict. Retirement writes status_updated_at as a
        # Timestamp and the link check as an ISO string (same-format strings compare
        # in time order), so both shapes get their own query.
        return [
            FieldFilter("last_scraped_update", ">=", since),
            FieldFilter("status_updated_at", ">=", since),
            FieldFilter("status_updated_at", ">=", since.astimezone(timezone.utc).isoformat()),
        ]
    if filters.agency:
        return [FieldFilter("agency", "in", chunk) for chunk in _chunks(filters.agency)]
    if filters.area:
        # planning_area is a string on some schemes and a list on others, in any case.
        areas = resolve_areas(filters.area, known_planning_areas(collection_ref))
        return [
            *(FieldFilter("planning_area", "array_contains_any", chunk) for chunk in _chunks(areas)),
            *(FieldFilter("planning_area", "in", chunk) for chunk in _chunks(areas)),
        ]
    return [FieldFilter("scheme_type", "array_contains_any", chunk) for chunk in _chunks(filters.scheme_types)]


def _sort_key(item: dict[str, Any]) -> tuple[datetime, str]:
    return as_datetime(item.get("last_scraped_update")) or _EPOCH, item["scheme_id"]


def get_filtered_results(
    collection_ref: Any,
    filters: CatalogFilters,
    *,
    fields: Sequence[str],
    cursor: str | None = None,
    limit: int = 10,
    exclude_statuses: frozenset[str] = frozenset(),
) -> PaginationResult:
    """Page through schemes matching ``filters``, newest scrape first.

    The cursor is the first scheme of the next page, as in ``get_paginated_results``.
    A cursor whose scheme is no longer in the result starts again at the first page.
    """
    if not filters.active:
        raise ValueError("get_filtered_results needs at least one active filter")
    projection = list(dict.fromkeys([*fields, "status", "last_scraped_update", "status_updated_at"]))

    candidates: dict[str, dict[str, Any]] = {}
    for field_filter in _candidate_filters(collection_ref, filters):
        for doc in collection_ref.where(filter=field_filter).select(projection).stream():
            candidates.setdefault(doc.id, {"scheme_id": doc.id, **(doc.to_dict() or {})})

    listed = sorted(
        (
            item
            for item in candidates.values()
            if item.get("status") not in exclude_statuses and matches(item, filters)
        ),
        key=_sort_key,
        reverse=True,
    )

    ids = [item["scheme_id"] for item in listed]
    cursor_id = _decode_cursor(cursor) if cursor else None
    start = ids.index(cursor_id) if cursor_id in ids else 0
    page = listed[start : start + limit]
    has_more = start + limit < len(listed)
    return PaginationResult(
        data=page,
        next_cursor=_encode_cursor(ids[start + limit]) if has_more else None,
        has_more=has_more,
        total_count=len(listed),
    )
