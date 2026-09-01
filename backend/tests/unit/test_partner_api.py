"""Unit tests for the partner API: routing, response allowlist, auth and rate limiting."""

import pytest
from partner.routing import Route, RouteError, resolve_route
from partner.serializers import PUBLIC_FIELDS, error_body, to_public_scheme
from utils.partner_auth import (
    DEFAULT_RATE_LIMIT_PER_MIN,
    check_and_increment_rate_limit,
    hash_key,
    verify_partner_key,
)


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/v1/schemes", "/v1/schemes/", "v1/schemes"])
def test_list_route(path):
    """A bare collection path lists, with or without a trailing slash."""
    assert resolve_route("GET", path) == Route(kind="list")


def test_detail_route_carries_the_id():
    assert resolve_route("GET", "/v1/schemes/abc123") == Route(kind="detail", scheme_id="abc123")


def test_search_route_is_post_only():
    assert resolve_route("POST", "/v1/schemes/search") == Route(kind="search")


def test_search_is_not_shadowed_by_a_scheme_called_search():
    """`search` is reserved, so GET on it must not resolve to a detail lookup."""
    result = resolve_route("GET", "/v1/schemes/search")
    assert isinstance(result, RouteError)
    assert result.status == 405


def test_missing_version_is_rejected():
    result = resolve_route("GET", "/schemes")
    assert isinstance(result, RouteError)
    assert result.code == "unsupported_version"
    assert result.status == 404


@pytest.mark.parametrize("path", ["/v2/schemes", "/v1.0/schemes", "/"])
def test_unknown_or_absent_version_is_rejected(path):
    """Never fall through to an implicit v1."""
    result = resolve_route("GET", path)
    assert isinstance(result, RouteError)
    assert result.code == "unsupported_version"


def test_unknown_resource_is_rejected():
    result = resolve_route("GET", "/v1/agencies")
    assert isinstance(result, RouteError)
    assert result.code == "not_found"


def test_too_many_segments_is_rejected():
    result = resolve_route("GET", "/v1/schemes/abc123/extra")
    assert isinstance(result, RouteError)
    assert result.code == "not_found"


@pytest.mark.parametrize(
    ("method", "path"),
    [("POST", "/v1/schemes"), ("DELETE", "/v1/schemes/abc"), ("GET", "/v1/schemes/search")],
)
def test_wrong_method_is_405(method, path):
    result = resolve_route(method, path)
    assert isinstance(result, RouteError)
    assert result.status == 405


# --------------------------------------------------------------------------
# Response allowlist
# --------------------------------------------------------------------------


INTERNAL_DOC = {
    "scheme": "Test Scheme",
    "description": "A description",
    "agency": "MSF",
    "link": "https://example.com",
    "phone": "1800-000-000",
    "email": "help@example.com",
    "status": "active",
    # Internal fields that must never reach a partner:
    "approved_by": "reviewer@better.sg",
    "scraped_text": "raw page dump ...",
    "source_entry_id": "schemeEntries/abc",
    "search_booster": "boost boost boost",
    "link_check_status_code": 200,
    "last_link_check": "2026-08-01",
    "last_scraped_update": "2026-08-01",
    "last_llm_processed_update": "2026-08-01",
}

LEAKY_FIELDS = [
    "approved_by",
    "scraped_text",
    "source_entry_id",
    "search_booster",
    "link_check_status_code",
    "last_link_check",
    "last_scraped_update",
    "last_llm_processed_update",
]


@pytest.mark.parametrize("field", LEAKY_FIELDS)
def test_internal_fields_are_never_serialized(field):
    public = to_public_scheme("doc-1", INTERNAL_DOC)
    assert field not in public


def test_serializer_output_is_exactly_the_allowlist():
    """No field outside the allowlist, and every allowlisted key present."""
    public = to_public_scheme("doc-1", INTERNAL_DOC)
    assert set(public) == set(PUBLIC_FIELDS)


def test_scheme_id_comes_from_the_document_id():
    public = to_public_scheme("doc-1", {**INTERNAL_DOC, "scheme_id": "stale-value"})
    assert public["scheme_id"] == "doc-1"


def test_unknown_extra_fields_are_dropped():
    """A field added to the doc later must not silently join the contract."""
    public = to_public_scheme("doc-1", {**INTERNAL_DOC, "some_new_internal_field": "x"})
    assert "some_new_internal_field" not in public


def test_error_body_shape():
    body = error_body("rate_limited", "Too many requests")
    assert body == {"error": {"code": "rate_limited", "message": "Too many requests"}}


def test_error_body_carries_extras():
    body = error_body("scheme_retired", "Retired", merged_into="new-id")
    assert body["error"]["merged_into"] == "new-id"


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


class FakeDoc:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class FakeDocRef:
    def __init__(self, store, key):
        self._store = store
        self._key = key

    def get(self):
        return FakeDoc(self._store.get(self._key))

    def set(self, data, merge=False):
        existing = self._store.get(self._key) or {}
        merged = {**existing, **data} if merge else dict(data)
        # Emulate firestore Increment sentinels used by the rate limiter.
        for field, value in data.items():
            if hasattr(value, "value"):
                merged[field] = (existing.get(field) or 0) + value.value
        self._store[self._key] = merged


class FakeCollection:
    def __init__(self, store):
        self._store = store

    def document(self, key):
        return FakeDocRef(self._store, key)


class FakeFirestore:
    def __init__(self, collections=None):
        self.collections = collections or {}

    def collection(self, name):
        return FakeCollection(self.collections.setdefault(name, {}))


class FakeRequest:
    def __init__(self, headers=None, method="GET", path="/v1/schemes", json_body=None):
        self.headers = headers or {}
        self.method = method
        self.path = path
        self._json = json_body

    def get_json(self, silent=False):
        return self._json


RAW_KEY = "sk_test_abc123"


def _db_with_key(**overrides):
    doc = {"consumer": "carecompass", "active": True, "rate_limit_per_min": 5}
    doc.update(overrides)
    return FakeFirestore({"partner_keys": {hash_key(RAW_KEY): doc}})


def test_valid_key_resolves_to_its_consumer():
    ok, consumer, limit = verify_partner_key(FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key())
    assert (ok, consumer, limit) == (True, "carecompass", 5)


def test_missing_key_is_rejected():
    ok, error, _ = verify_partner_key(FakeRequest(), _db_with_key())
    assert (ok, error) == (False, "missing_key")


def test_unknown_key_is_rejected():
    ok, error, _ = verify_partner_key(FakeRequest({"X-API-Key": "nope"}), _db_with_key())
    assert (ok, error) == (False, "invalid_key")


def test_revoked_key_is_rejected_distinctly():
    """A revoked key is 403, not 401 — the partner needs to know it existed."""
    ok, error, _ = verify_partner_key(FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(active=False))
    assert (ok, error) == (False, "revoked_key")


@pytest.mark.parametrize("active", ["false", "true", 1, 0, "", None, "yes"])
def test_only_a_real_boolean_true_authenticates(active):
    """Revocation is done by hand in the console, so `active` can be junk.

    Anything other than boolean True must fail closed — the string "false" is
    truthy, and a truthiness check would have kept a revoked key working.
    """
    ok, error, _ = verify_partner_key(FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(active=active))
    assert (ok, error) == (False, "revoked_key")


def test_zero_rate_limit_is_honoured_not_defaulted():
    """0 means "throttled to a standstill", a softer option than revoking."""
    ok, consumer, limit = verify_partner_key(
        FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(rate_limit_per_min=0)
    )
    assert (ok, consumer, limit) == (True, "carecompass", 0)
    assert check_and_increment_rate_limit(FakeFirestore(), consumer, limit) == (False, 0)


def test_missing_rate_limit_falls_back_to_the_default():
    _, _, limit = verify_partner_key(
        FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(rate_limit_per_min=None)
    )
    assert limit == DEFAULT_RATE_LIMIT_PER_MIN


def test_unparseable_rate_limit_falls_back_instead_of_raising():
    """A hand-typed value must not turn every partner request into a 500."""
    _, _, limit = verify_partner_key(
        FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(rate_limit_per_min="lots")
    )
    assert limit == DEFAULT_RATE_LIMIT_PER_MIN


def test_negative_rate_limit_clamps_to_zero():
    _, _, limit = verify_partner_key(
        FakeRequest({"X-API-Key": RAW_KEY}), _db_with_key(rate_limit_per_min=-5)
    )
    assert limit == 0


def test_header_lookup_is_case_insensitive():
    ok, consumer, _ = verify_partner_key(FakeRequest({"x-api-key": RAW_KEY}), _db_with_key())
    assert (ok, consumer) == (True, "carecompass")


def test_raw_key_is_never_the_document_id():
    db = _db_with_key()
    assert RAW_KEY not in db.collections["partner_keys"]
    assert hash_key(RAW_KEY) in db.collections["partner_keys"]


# --------------------------------------------------------------------------
# Rate limiting
# --------------------------------------------------------------------------


def test_rate_limit_counts_down_then_blocks():
    db = FakeFirestore()
    seen = [check_and_increment_rate_limit(db, "carecompass", 3) for _ in range(4)]
    assert [(ok, remaining) for ok, remaining in seen] == [
        (True, 2),
        (True, 1),
        (True, 0),
        (False, 0),
    ]


def test_rate_limit_budget_is_per_consumer():
    db = FakeFirestore()
    check_and_increment_rate_limit(db, "carecompass", 1)
    ok, remaining = check_and_increment_rate_limit(db, "compassion-collective", 1)
    assert (ok, remaining) == (True, 0)


def test_rate_limit_is_shared_across_operations():
    """One budget per partner, not one per endpoint."""
    db = FakeFirestore()
    check_and_increment_rate_limit(db, "carecompass", 2)  # e.g. a list call
    ok, remaining = check_and_increment_rate_limit(db, "carecompass", 2)  # e.g. a search call
    assert (ok, remaining) == (True, 0)
    assert check_and_increment_rate_limit(db, "carecompass", 2)[0] is False
