"""Unit tests for partner API handlers and the lazy-import boundary."""

import base64
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from partner.api import _dispatch, _handle_detail, _handle_list
from partner.routing import Route
from partner.serializers import PUBLIC_FIELDS, PartnerRequestError, clamp_limit
from utils.catalog_pagination import PaginationResult, _encode_cursor
from utils.pagination import encode_cursor as encode_search_cursor
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES


FUNCTIONS_DIR = Path(__file__).resolve().parents[2] / "functions"


class FakeDoc:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class FakeDocRef:
    def __init__(self, doc):
        self._doc = doc

    def get(self):
        return self._doc


class FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def document(self, doc_id):
        return FakeDocRef(FakeDoc(doc_id, self._docs.get(doc_id)))


class FakeFirestore:
    def __init__(self, docs):
        self._docs = docs

    def collection(self, _name):
        return FakeCollection(self._docs)


ACTIVE = {"scheme": "Active Scheme", "status": "active", "approved_by": "reviewer@better.sg"}
INACTIVE = {"scheme": "Dead Link Scheme", "status": "inactive"}
RETIRED_MERGED = {"scheme": "Old", "status": "retired", "merged_into": "new-scheme-id"}
RETIRED_ALONE = {"scheme": "Old", "status": "retired"}


def _db(**docs):
    return FakeFirestore(docs)


class _Args:
    """Stand-in for werkzeug's request.args (a MultiDict) in list tests."""

    def __init__(self, values):
        self._values = values

    def get(self, key, default=None):
        return self._values.get(key, default)

    def keys(self):
        return self._values.keys()


class _SearchRequest:
    """Minimal POST /v1/schemes/search request carrying an arbitrary JSON body."""

    method = "POST"
    path = "/v1/schemes/search"

    def __init__(self, body):
        self._body = body

    def get_json(self, silent=False):
        return self._body


def test_active_scheme_returns_allowlisted_payload():
    body, status = _handle_detail(_db(**{"s1": ACTIVE}), "s1")
    assert status == 200
    assert set(body["data"]) == set(PUBLIC_FIELDS)
    assert body["data"]["scheme_id"] == "s1"
    assert "approved_by" not in body["data"]


def test_missing_scheme_is_404():
    body, status = _handle_detail(_db(), "nope")
    assert status == 404
    assert body["error"]["code"] == "not_found"


def test_inactive_scheme_is_404_with_no_pointer():
    """`inactive` is hidden from partners even though no existing read path hides it."""
    body, status = _handle_detail(_db(**{"s1": INACTIVE}), "s1")
    assert status == 404
    assert body["error"]["code"] == "not_found"
    assert "merged_into" not in body["error"]


def test_retired_and_merged_scheme_returns_the_merge_target():
    body, status = _handle_detail(_db(**{"s1": RETIRED_MERGED}), "s1")
    assert status == 404
    assert body["error"]["code"] == "scheme_retired"
    assert body["error"]["merged_into"] == "new-scheme-id"


def test_retired_without_merge_gives_no_pointer():
    body, status = _handle_detail(_db(**{"s1": RETIRED_ALONE}), "s1")
    assert status == 404
    assert body["error"]["code"] == "not_found"
    assert "merged_into" not in body["error"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 10), ("5", 5), (5, 5), ("0", 1), ("-3", 1), ("9999", 50), (50, 50)],
)
def test_limit_is_clamped(raw, expected):
    assert clamp_limit(raw, default=10) == expected


def test_clamp_limit_honours_the_callers_default():
    """list and search have different page sizes, so the default is passed in."""
    assert clamp_limit(None, default=20) == 20


def test_non_numeric_limit_is_rejected():
    with pytest.raises(PartnerRequestError):
        clamp_limit("many", default=10)


# --------------------------------------------------------------------------
# List
# --------------------------------------------------------------------------


def test_list_refills_the_page_past_inactive_and_retired(mocker):
    """Partners must get full pages, not pages with the hidden rows punched out.

    Regression guard: filtering the returned page instead of passing the excluded
    statuses down produced short pages (a limit=2 request answering with 1 item).
    """
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        side_effect=[
            PaginationResult(
                data=[
                    {"scheme_id": "gone", "status": "retired"},
                    {"scheme_id": "dead-link", "status": "inactive"},
                ],
                next_cursor="next",
                has_more=True,
            ),
            PaginationResult(
                data=[
                    {"scheme_id": "live-a", "status": "active"},
                    {"scheme_id": "live-b", "status": "active"},
                ],
                has_more=False,
            ),
        ],
    )
    mocker.patch("schemes.catalog._count_excluded_schemes", return_value=0)

    body = _handle_list(MagicMock(), _Args({"limit": "2"}))

    assert [item["scheme_id"] for item in body["data"]] == ["live-a", "live-b"]


def test_list_total_count_excludes_what_the_list_hides(mocker):
    """total_count must describe the reachable corpus, not the raw collection.

    12 of 214 schemes are inactive or retired, so a partner paginating to
    total_count must be told 202 — otherwise it never terminates.
    """
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[{"scheme_id": "live", "status": "active"}],
            has_more=False,
            total_count=214,
        ),
    )
    counted = mocker.patch("schemes.catalog._count_excluded_schemes", return_value=12)

    body = _handle_list(MagicMock(), _Args({"limit": "1"}))

    assert body["total_count"] == 202
    # The count must span both hidden statuses, not just retired.
    assert counted.call_args.args[2] == NON_SEARCHABLE_STATUSES


def test_foreign_value_error_is_not_echoed_to_the_partner(mocker):
    """A ValueError from shared/third-party code must not become a 400 body.

    CodeQL flagged the old `except ValueError: str(exc)` handler as stack-trace
    exposure. The risk was concrete: the partner call path runs Firestore, pandas
    and the shared catalog helpers, so an internal message would have been handed
    over verbatim. Only PartnerRequestError is client-facing now.
    """
    secret = "internal detail: /srv/functions/secret_field mismatch"
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        side_effect=ValueError(secret),
    )

    with pytest.raises(ValueError) as excinfo:
        _handle_list(MagicMock(), _Args({"limit": "5"}))

    # It escapes as a plain ValueError, which partner_api turns into a logged 500,
    # rather than as a PartnerRequestError that would be rendered into the body.
    assert not isinstance(excinfo.value, PartnerRequestError)
    assert secret in str(excinfo.value)


def test_invalid_filter_value_is_restated_not_forwarded(mocker):
    """An unknown category is still a 400, but with a message authored here.

    Only ``spec.normalize`` is inside the try, and the sole ValueError any
    normalizer raises is ``_expand_category``'s unknown-category — a client
    mistake. Whatever the wording, it is never forwarded: the 400 body carries the
    message built here, so this stays safe even if a normalizer someday raises for
    another reason.
    """
    spec = MagicMock()
    spec.normalize.side_effect = ValueError("Unknown category: 'healthcare'")
    mocker.patch("schemes.catalog.FILTER_SPECS", {"category": spec})
    mocker.patch("partner.api.FILTER_SPECS", {"category": spec})

    with pytest.raises(PartnerRequestError) as excinfo:
        _handle_list(MagicMock(), _Args({"category": "healthcare"}))

    message = excinfo.value.client_message
    assert "category" in message and "healthcare" in message
    # The shared module's own wording is not forwarded.
    assert "Unknown category" not in message


def test_list_rejects_unknown_query_parameters():
    with pytest.raises(PartnerRequestError, match="sort"):
        _handle_list(MagicMock(), _Args({"sort": "name"}))


def test_list_rejects_combining_filters():
    with pytest.raises(PartnerRequestError):
        _handle_list(MagicMock(), _Args({"agency": "MOH", "area": "BEDOK"}))


@pytest.mark.parametrize(
    "cursor",
    [
        "!!!not-base64!!!",
        base64.urlsafe_b64encode(b'{"data": {"doc_id": "x"}}').decode(),  # no signature
        base64.urlsafe_b64encode(b'{"data": {"doc_id": "x"}, "signature": "bad"}').decode(),
        base64.urlsafe_b64encode(b"not json at all").decode(),
    ],
    ids=["malformed", "unsigned", "wrong-signature", "not-json"],
)
def test_list_rejects_a_cursor_we_did_not_issue(cursor, mocker):
    """A bad cursor must 400, not silently rewind to page one.

    `_get_paginated_query` falls back to the first page for any cursor it cannot
    verify. For /catalog that is fine. For a partner it means page one comes back
    with 200 and a fresh next_cursor, so a client whose cursor got truncated
    re-reads page one indefinitely and never sees an error.

    Patched so a leaked-through cursor would still not reach Firestore.
    """
    paginate = mocker.patch(
        # partner.api imported the name directly, so patch it there. Patching
        # schemes.catalog leaves partner.api's reference bound to the real function.
        "partner.api._get_listed_paginated_results",
        return_value=PaginationResult(data=[], next_cursor=None, has_more=False, total_count=0),
    )
    with pytest.raises(PartnerRequestError, match="Invalid cursor"):
        _handle_list(MagicMock(), _Args({"cursor": cursor}))
    paginate.assert_not_called()


def test_list_accepts_a_cursor_we_issued(mocker):
    """The guard must not reject our own tokens — the round trip has to hold."""
    mocker.patch(
        # partner.api imported the name directly, so patch it there. Patching
        # schemes.catalog leaves partner.api's reference bound to the real function.
        "partner.api._get_listed_paginated_results",
        return_value=PaginationResult(data=[], next_cursor=None, has_more=False, total_count=0),
    )
    _handle_list(MagicMock(), _Args({"cursor": _encode_cursor("some-doc-id")}))


def test_an_empty_cursor_parameter_is_rejected_not_ignored(mocker):
    """`?cursor=` is a cursor truncated to nothing, and the docs promise a 400.

    A `cursor` that is absent still means "first page"; only a present-but-empty
    value is an error. Otherwise the one truncation a partner is most likely to hit
    is the one case that silently rewinds.
    """
    paginate = mocker.patch("partner.api._get_listed_paginated_results")
    with pytest.raises(PartnerRequestError, match="Invalid cursor"):
        _handle_list(MagicMock(), _Args({"cursor": ""}))
    paginate.assert_not_called()


def test_an_absent_cursor_still_means_the_first_page(mocker):
    """The counterpart: omitting the parameter must not become an error."""
    paginate = mocker.patch(
        "partner.api._get_listed_paginated_results",
        return_value=PaginationResult(data=[], next_cursor=None, has_more=False, total_count=0),
    )
    _handle_list(MagicMock(), _Args({"limit": "5"}))
    assert paginate.call_args.kwargs["cursor"] is None


def test_list_cursor_guard_runs_after_the_cheaper_checks():
    """Ordering matters: an unknown parameter is reported even with a bad cursor.

    Otherwise a partner sending both gets told only about the cursor, fixes it, and
    then discovers the parameter problem on the next round trip.
    """
    with pytest.raises(PartnerRequestError, match="sort"):
        _handle_list(MagicMock(), _Args({"sort": "name", "cursor": "!!!bogus!!!"}))


@pytest.mark.parametrize("body", [["not", "an", "object"], "a string", 42, True])
def test_non_object_search_body_is_a_client_error(body):
    """A valid-JSON non-object body must be a 400, not an AttributeError 500.

    Asserted through _dispatch so it also proves the check runs *before* the lazy
    search import — a bad body must not cost an embeddings load.
    """
    request = _SearchRequest(body)
    with pytest.raises(PartnerRequestError, match="must be a JSON object"):
        _dispatch(Route(kind="search"), request, _db(), {})


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------


def _stub_search_model(mocker, records):
    """Install a fake search.retriever so handle_search runs without loading torch."""
    import pandas as pd

    model = MagicMock()
    model.return_value.aggregate_and_rank_results.return_value = pd.DataFrame(records)
    mocker.patch.dict(sys.modules, {"search.retriever": MagicMock(SearchModel=model)})
    return model


def test_search_hides_inactive_and_retired_results(mocker):
    """The ranker has no lifecycle opinion, so the handler must apply one."""
    _stub_search_model(
        mocker,
        [
            {"scheme_id": "live", "status": "active", "scheme": "Live"},
            {"scheme_id": "dead-link", "status": "inactive", "scheme": "Dead"},
            {"scheme_id": "gone", "status": "retired", "scheme": "Gone"},
        ],
    )
    from partner.search import handle_search

    body = handle_search(MagicMock(), {"query": "eldercare"})

    assert [item["scheme_id"] for item in body["data"]] == ["live"]
    # total_count must describe what survived the filter, not what the ranker returned.
    assert body["total_count"] == 1


def test_search_returns_an_empty_page_when_the_ranker_finds_nothing(mocker):
    _stub_search_model(mocker, [])
    from partner.search import handle_search

    body = handle_search(MagicMock(), {"query": "no such thing"})

    assert body["data"] == []
    assert body["has_more"] is False


@pytest.mark.parametrize("query", [None, "", "   ", 0])
def test_search_requires_a_non_empty_query(mocker, query):
    _stub_search_model(mocker, [])
    from partner.search import handle_search

    with pytest.raises(PartnerRequestError, match="query"):
        handle_search(MagicMock(), {"query": query})


@pytest.mark.parametrize(
    ("raw", "expected_len"),
    [(None, 3), ("2", 2), (0, 1), (-1, 1), (9999, 3)],
)
def test_search_limit_is_clamped(mocker, raw, expected_len):
    """Search keeps its own page-size ceiling, independent of the list route."""
    _stub_search_model(
        mocker,
        [{"scheme_id": f"s{i}", "status": "active", "scheme": f"S{i}"} for i in range(3)],
    )
    from partner.search import handle_search

    body = handle_search(MagicMock(), {"query": "eldercare", "limit": raw})

    assert len(body["data"]) == expected_len


def test_search_rejects_a_non_numeric_limit(mocker):
    _stub_search_model(mocker, [])
    from partner.search import handle_search

    with pytest.raises(PartnerRequestError, match="limit"):
        handle_search(MagicMock(), {"query": "eldercare", "limit": "many"})


def test_search_rejects_a_list_cursor(mocker):
    """A cursor from the other operation must 400, not quietly serve page one.

    Both codecs sign with the same CURSOR_SECRET, so a list cursor passes the
    *signature* check on the search path. `get_paginated_results` then finds no
    scheme_id/similarity_score and falls back to the first page with a 200 — the
    original defect, reached by the plausible mistake of pasting a list next_cursor
    into a search request. So the guard checks the payload, not just the signature.
    """
    model = _stub_search_model(mocker, [{"scheme_id": "live", "status": "active"}])
    from partner.search import handle_search

    with pytest.raises(PartnerRequestError, match="Invalid cursor"):
        handle_search(MagicMock(), {"query": "eldercare", "cursor": _encode_cursor("a-doc-id")})

    model.return_value.aggregate_and_rank_results.assert_not_called()


def test_list_rejects_a_search_cursor():
    """The mirror case. Guarded already, because the doc_id lookup returns None."""
    with pytest.raises(PartnerRequestError, match="Invalid cursor"):
        _handle_list(MagicMock(), _Args({"cursor": encode_search_cursor("s1", 0.9, "sess")}))


def test_both_operations_agree_on_cursor_versus_limit_precedence(mocker):
    """A request with a bad cursor *and* a bad limit must name the same field.

    The two operations validate independently, so without this they can disagree —
    a partner fixing what list told them then hits a different error from search.
    """
    _stub_search_model(mocker, [])
    mocker.patch("partner.api._get_listed_paginated_results")
    from partner.search import handle_search

    both_wrong = {"cursor": "!!!bogus!!!", "limit": "many"}

    with pytest.raises(PartnerRequestError, match="Invalid cursor") as from_list:
        _handle_list(MagicMock(), _Args(both_wrong))
    with pytest.raises(PartnerRequestError, match="Invalid cursor") as from_search:
        handle_search(MagicMock(), {"query": "eldercare", **both_wrong})

    assert from_list.value.client_message == from_search.value.client_message


def test_search_rejects_a_bad_cursor_before_it_ranks(mocker):
    """A bad cursor must 400, and must not cost a ranking pass to find out.

    `get_paginated_results` ignores a cursor it cannot verify and returns page one,
    so without this guard a partner re-reads page one forever with 200s.
    """
    model = _stub_search_model(mocker, [{"scheme_id": "live", "status": "active"}])
    from partner.search import handle_search

    with pytest.raises(PartnerRequestError, match="Invalid cursor"):
        handle_search(MagicMock(), {"query": "elderly medical bills", "cursor": "!!!bogus!!!"})

    model.return_value.aggregate_and_rank_results.assert_not_called()


def test_search_never_leaks_internal_fields(mocker):
    """The ranker's frame carries internal columns; none may reach a partner."""
    _stub_search_model(
        mocker,
        [
            {
                "scheme_id": "live",
                "status": "active",
                "scheme": "Live",
                "approved_by": "reviewer@better.sg",
                "scraped_text": "raw page dump",
                "search_booster": 3,
            }
        ],
    )
    from partner.search import handle_search

    record = handle_search(MagicMock(), {"query": "eldercare"})["data"][0]

    assert set(record) <= set(PUBLIC_FIELDS)
    for leaked in ("approved_by", "scraped_text", "search_booster"):
        assert leaked not in record


def test_importing_the_api_does_not_load_the_search_stack():
    """`partner.api` must keep the embeddings stack out of its own import graph.

    Scope note: this proves module-level hygiene for *this* module, not that a
    real cold start avoids the load. It does not, today — main.py imports
    agent.handler, which imports search.retriever, so the whole deployment pays
    it regardless. This guard is what keeps the partner side from adding a second
    reason to, and makes the win real once agent.handler defers its own import.

    Run in a subprocess so the assertion is about a clean interpreter, not about
    whatever the rest of the test session happens to have imported already.
    """
    # Acceptance criterion 7 names `GET /v1/schemes` specifically, so the probe
    # goes through _dispatch on the *list* branch — the function that holds the
    # lazy import — and through detail, rather than only calling a leaf handler.
    preamble = (
        "class _Doc:\n"
        "    exists = False\n"
        "    id = 'nope'\n"
        "    def to_dict(self): return None\n"
        "class _Ref:\n"
        "    def get(self): return _Doc()\n"
        "class _Col:\n"
        "    def document(self, _id): return _Ref()\n"
        "class _Db:\n"
        "    def collection(self, _name): return _Col()\n"
        "class _Args(dict):\n"
        "    pass\n"
        "class _Req:\n"
        "    method = 'GET'\n"
        "    path = '/v1/schemes'\n"
        "    args = _Args()\n"
    )
    probe = (
        "import sys;"
        "import partner.api as api;"
        "from partner.routing import Route, resolve_route;"
        "from utils.catalog_pagination import PaginationResult;"
        # Patched at the catalog seam so the probe needs no Firestore fake for
        # pagination. Everything between _dispatch and here is the real code.
        "setattr(api, '_get_listed_paginated_results',"
        " lambda **kw: PaginationResult(data=[], has_more=False, total_count=0));"
        "assert resolve_route('GET', '/v1/schemes') == Route(kind='list');"
        "api._dispatch(Route(kind='list'), _Req(), _Db(), {});"
        "api._handle_detail(_Db(), 'nope');"
        "heavy = [m for m in"
        " ('search.retriever', 'search', 'torch', 'sentence_transformers', 'faiss')"
        " if m in sys.modules];"
        "assert not heavy, heavy;"
        "print('clean')"
    )
    probe = preamble + probe
    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=FUNCTIONS_DIR,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout
