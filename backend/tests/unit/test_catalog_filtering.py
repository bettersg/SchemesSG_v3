"""Unit tests for multi-filter catalog listing (#484)."""

from datetime import datetime, timezone

import pytest
from utils import catalog_filtering
from utils.catalog_filtering import (
    CatalogFilters,
    agency_key,
    as_datetime,
    get_filtered_results,
    parse_updated_since,
    resolve_agencies,
    resolve_areas,
    updated_at,
)
from utils.catalog_pagination import _decode_cursor, _encode_cursor


UTC = timezone.utc


@pytest.fixture(autouse=True)
def _clear_known_values_cache():
    catalog_filtering._known_cache.clear()
    yield
    catalog_filtering._known_cache.clear()


class _Doc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    def to_dict(self):
        return dict(self._data)


def _firestore_match(value, op, operand):
    """Firestore semantics for the operators this module issues, type-strict like the real thing."""
    if op == "in":
        return not isinstance(value, list) and value in operand
    if op == "array_contains_any":
        return isinstance(value, list) and bool(set(value) & set(operand))
    if op == ">=":
        same_type = (isinstance(value, datetime) and isinstance(operand, datetime)) or (
            isinstance(value, str) and isinstance(operand, str)
        )
        return same_type and value >= operand
    raise AssertionError(f"unexpected operator {op}")


class _Query:
    def __init__(self, docs, field_filter=None):
        self._docs = docs
        self._filter = field_filter
        self.projection = None

    def select(self, fields):
        self.projection = list(fields)
        return self

    def stream(self):
        f = self._filter
        for doc_id, data in self._docs.items():
            if f is None or (f.field_path in data and _firestore_match(data[f.field_path], f.op_string, f.value)):
                yield _Doc(doc_id, {k: v for k, v in data.items() if k in self.projection})


class _Collection:
    def __init__(self, docs):
        self.docs = docs
        self.filters = []

    def where(self, *, filter):
        self.filters.append(filter)
        return _Query(self.docs, filter)

    def select(self, fields):
        return _Query(self.docs).select(fields)


def _ts(day):
    return datetime(2026, 10, day, tzinfo=UTC)


DOCS = {
    # planning_area is a plain string on most schemes and a list on the rest
    "string-area": {
        "agency": "PAVE",
        "planning_area": "BEDOK",
        "scheme_type": ["Healthcare"],
        "status": "active",
        "last_scraped_update": _ts(10),
    },
    "list-area": {
        "agency": "TOUCH Community Services",
        "planning_area": ["BEDOK", "TAMPINES"],
        "scheme_type": ["Caregiver Support"],
        "status": None,
        "last_scraped_update": _ts(12),
    },
    "other-area": {
        "agency": "Touch Community Services",
        "planning_area": "JURONG WEST",
        "scheme_type": ["Caregiver Support"],
        "status": "active",
        "last_scraped_update": _ts(11),
    },
    "inactive": {
        "agency": "PAVE",
        "planning_area": "BEDOK",
        "scheme_type": ["Healthcare"],
        "status": "inactive",
        # legacy import map, as on 428 dev schemes
        "last_scraped_update": {"_seconds": 1758460098, "_nanoseconds": 0},
        "status_updated_at": "2026-10-20T09:00:00.000000+00:00",
    },
    # Retirement writes status_updated_at as a Timestamp, the link check as an ISO string.
    "retired": {
        "agency": "PAVE",
        "planning_area": "TUAS",
        "scheme_type": ["Healthcare"],
        "status": "retired",
        "last_scraped_update": _ts(1),
        "status_updated_at": _ts(21),
    },
}

FIELDS = ("agency", "planning_area", "scheme_type")


def _ids(result):
    return [item["scheme_id"] for item in result.data]


# ------------------------------------------------------------------ timestamps


@pytest.mark.parametrize(
    "value, expected",
    [
        (_ts(1), _ts(1)),
        (datetime(2026, 10, 1), _ts(1)),
        ({"_seconds": 1758460098, "_nanoseconds": 500_000_000}, datetime.fromtimestamp(1758460098.5, tz=UTC)),
        ("2026-10-01T00:00:00+00:00", _ts(1)),
        ("2026-10-01T00:00:00Z", _ts(1)),
        ("2026-10-01", _ts(1)),
        ("not a date", None),
        (None, None),
        (float("nan"), None),
    ],
)
def test_as_datetime_reads_every_stored_shape(value, expected):
    assert as_datetime(value) == expected


def test_updated_at_takes_the_later_of_scrape_and_status_change():
    assert updated_at(DOCS["inactive"]) == datetime(2026, 10, 20, 9, tzinfo=UTC)
    assert updated_at(DOCS["string-area"]) == _ts(10)
    assert updated_at({}) is None


def test_parse_updated_since_rejects_non_iso():
    assert parse_updated_since(" 2026-10-01 ") == _ts(1)
    with pytest.raises(ValueError):
        parse_updated_since("last week")


# ------------------------------------------------------------------ agencies


def test_agency_key_ignores_case_punctuation_and_bracketed_abbreviation():
    assert agency_key("TOUCH Community Services") == agency_key("Touch Community Services")
    assert agency_key("Agency for Integrated Care (AIC)") == agency_key("agency for integrated care")
    assert agency_key("PAVE") != agency_key("PA")


def test_resolve_agencies_returns_every_stored_spelling():
    known = ["TOUCH Community Services", "Touch Community Services", "PAVE"]
    assert resolve_agencies(["touch community services"], known) == known[:2]
    assert resolve_agencies(["pave"], known) == ["PAVE"]
    # unknown agency is kept so the query returns nothing instead of dropping the filter
    assert resolve_agencies(["Nobody"], known) == ["Nobody"]


def test_resolve_areas_adds_every_stored_spelling():
    known = ["BEDOK", "Bedok", "bedok", "TAMPINES"]
    assert resolve_areas(["BEDOK"], known) == ["BEDOK", "Bedok", "bedok"]
    assert resolve_areas(["TUAS"], known) == ["TUAS"]


# ------------------------------------------------------------------ filtered listing


def test_area_matches_string_and_list_planning_areas():
    """array_contains alone missed every scheme that stores planning_area as a string."""
    col = _Collection(DOCS)
    result = get_filtered_results(
        col, CatalogFilters(area=("BEDOK",)), fields=FIELDS, exclude_statuses=frozenset({"inactive", "retired"})
    )

    assert _ids(result) == ["list-area", "string-area"]  # newest scrape first
    assert {f.op_string for f in col.filters} == {"array_contains_any", "in"}
    assert result.total_count == 2


def test_filters_and_together_and_values_or_within():
    col = _Collection(DOCS)
    result = get_filtered_results(
        col,
        CatalogFilters(area=("BEDOK", "JURONG WEST"), scheme_types=("Caregiver Support",)),
        fields=FIELDS,
        exclude_statuses=frozenset({"inactive", "retired"}),
    )

    assert _ids(result) == ["list-area", "other-area"]


def test_agency_filter_drives_the_firestore_query():
    col = _Collection(DOCS)
    result = get_filtered_results(
        col,
        CatalogFilters(agency=("PAVE",), area=("BEDOK",)),
        fields=FIELDS,
        exclude_statuses=frozenset({"inactive", "retired"}),
    )

    assert [(f.field_path, f.op_string) for f in col.filters] == [("agency", "in")]
    assert _ids(result) == ["string-area"]


def test_updated_since_unions_both_timestamps_and_keeps_removed_schemes():
    col = _Collection(DOCS)
    result = get_filtered_results(col, CatalogFilters(updated_since=_ts(11)), fields=FIELDS)

    assert [f.field_path for f in col.filters] == ["last_scraped_update", "status_updated_at", "status_updated_at"]
    assert set(_ids(result)) == {"list-area", "other-area", "inactive", "retired"}
    assert all("status_updated_at" in item for item in result.data if item["scheme_id"] == "inactive")


def test_paging_in_memory_walks_every_result_once():
    """The cursor names the first scheme of the next page, as in Firestore paging."""
    order = ["list-area", "other-area", "string-area", "inactive"]  # newest scrape first, legacy map last
    col = _Collection(DOCS)
    seen, cursor = [], None
    while True:
        page = get_filtered_results(
            col, CatalogFilters(area=("BEDOK", "JURONG WEST")), fields=FIELDS, cursor=cursor, limit=1
        )
        seen += _ids(page)
        assert page.total_count == 4
        if not page.has_more:
            break
        cursor = page.next_cursor
        assert _decode_cursor(cursor) == order[len(seen)]

    assert seen == order


def test_unknown_cursor_restarts_at_the_first_page():
    col = _Collection(DOCS)
    page = get_filtered_results(
        col, CatalogFilters(area=("BEDOK",)), fields=FIELDS, cursor=_encode_cursor("deleted"), limit=1
    )
    assert _ids(page) == ["list-area"]


def test_more_than_thirty_values_are_split_across_queries():
    col = _Collection(DOCS)
    areas = tuple(f"AREA {i}" for i in range(31)) + ("BEDOK",)
    get_filtered_results(col, CatalogFilters(area=areas), fields=FIELDS)

    assert all(len(f.value) <= 30 for f in col.filters)
    assert len(col.filters) == 4  # two chunks, each as array_contains_any and in


def test_needs_an_active_filter():
    with pytest.raises(ValueError):
        get_filtered_results(_Collection(DOCS), CatalogFilters(), fields=FIELDS)


MIXED_CASE_DOCS = {
    # The Slack approval modal stores planning area as typed.
    "title-case": {
        "agency": "PAVE",
        "planning_area": "Bedok",
        "scheme_type": ["Healthcare"],
        "status": "active",
        "last_scraped_update": _ts(10),
    },
    "title-case-list": {
        "agency": "PAVE",
        "planning_area": ["Bedok"],
        "scheme_type": ["Healthcare"],
        "status": "active",
        "last_scraped_update": _ts(9),
    },
    "upper-case": {
        "agency": "Other",
        "planning_area": "BEDOK",
        "scheme_type": ["Healthcare"],
        "status": "active",
        "last_scraped_update": _ts(8),
    },
}


@pytest.mark.parametrize(
    "filters, expected",
    [
        (CatalogFilters(area=("BEDOK",)), ["title-case", "title-case-list", "upper-case"]),
        (CatalogFilters(agency=("PAVE",), area=("BEDOK",)), ["title-case", "title-case-list"]),
    ],
    ids=["area-only", "area-and-agency"],
)
def test_area_matches_stored_spellings_whichever_filter_fetches_candidates(filters, expected):
    """The result must not depend on whether area or agency drives the Firestore query."""
    result = get_filtered_results(_Collection(MIXED_CASE_DOCS), filters, fields=FIELDS)

    assert _ids(result) == expected
