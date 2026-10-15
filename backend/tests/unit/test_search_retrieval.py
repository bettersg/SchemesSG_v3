"""Unit tests for the vector retrieval step (SearchModel.search).

Behaviour under test: retrieval asks Firestore for the real cosine distance and
turns a closer match into a higher relevance score. Firestore is mocked so no
live index is needed.
"""

import pytest
from search.retriever import RETRIEVAL_LIMIT, SearchModel, fetch_schemes_by_ids


def _fake_doc(doc_id, distance):
    class _Doc:
        id = doc_id

        def to_dict(self):
            return {"vector_distance": distance}

    return _Doc()


def _fake_scheme_doc(doc_id, data, *, exists=True):
    class _Doc:
        id = doc_id

        def to_dict(self):
            return data.copy()

    doc = _Doc()
    doc.exists = exists
    return doc


@pytest.fixture
def model(mocker):
    mocker.patch.object(SearchModel, "initialise", return_value=None)
    SearchModel._instance = None
    SearchModel.initialised = True
    m = SearchModel(mocker.MagicMock())
    m.query_cache = {}
    # Embedding step returns a dummy vector.
    m.__class__.embeddings = mocker.MagicMock()
    m.__class__.embeddings.embed_query.return_value = [0.0, 0.0, 0.0]
    m.__class__.db = mocker.MagicMock()
    collection = m.__class__.db.collection.return_value
    collection.select.return_value = collection
    return m


def test_search_preserves_real_distance_as_relevance(model, mocker):
    """A nearer doc (smaller cosine distance) gets a higher relevance score."""
    near, far = _fake_doc("near", 0.1), _fake_doc("far", 0.9)
    model.__class__.db.collection.return_value.find_nearest.return_value.get.return_value = [near, far]

    # Fetch step returns scheme rows for the two ids.
    mocker.patch.object(
        model,
        "fetch_schemes_batch",
        return_value=[
            {"scheme_id": "near", "search_booster": "x"},
            {"scheme_id": "far", "search_booster": "y"},
        ],
    )

    merged = model.search("a query")
    scores = dict(zip(merged["scheme_id"], merged["vec_similarity_score"]))

    assert scores["near"] > scores["far"]


def test_retrieval_limit_within_firestore_maximum():
    """Firestore rejects find_nearest.limit above 1000, so the sentinel must not exceed it."""
    assert RETRIEVAL_LIMIT <= 1000


def test_search_requests_full_pool_and_distance_field(model, mocker):
    """Retrieval asks for the wide pool and the real distance field."""
    model.__class__.db.collection.return_value.find_nearest.return_value.get.return_value = [
        _fake_doc("a", 0.2)
    ]
    mocker.patch.object(
        model, "fetch_schemes_batch", return_value=[{"scheme_id": "a", "search_booster": "x"}]
    )

    model.search("a query")

    _, kwargs = model.__class__.db.collection.return_value.find_nearest.call_args
    assert kwargs["limit"] == RETRIEVAL_LIMIT
    assert kwargs["distance_result_field"] == "vector_distance"


def test_search_projects_only_distance(model, mocker):
    collection = model.__class__.db.collection.return_value
    collection.find_nearest.return_value.get.return_value = [_fake_doc("a", 0.2)]
    mocker.patch.object(model, "fetch_schemes_batch", return_value=[{"scheme_id": "a", "search_booster": "x"}])

    result = model.search("a query")

    collection.select.assert_called_once_with(["vector_distance"])
    assert result["scheme_id"].tolist() == ["a"]
    assert result["vec_similarity_score"].tolist() == [1.0]


def test_empty_projected_results_skip_hydration(model, mocker):
    model.__class__.db.collection.return_value.find_nearest.return_value.get.return_value = []
    fetch = mocker.patch.object(model, "fetch_schemes_batch")

    assert model.search("a query").empty
    fetch.assert_not_called()


def test_scheme_hydration_uses_get_all_and_preserves_requested_order(mocker):
    firestore = mocker.MagicMock()
    firestore.get_all.return_value = [
        _fake_scheme_doc("second", {"scheme": "Second", "scraped_text": "large"}),
        _fake_scheme_doc("retired", {"scheme": "Retired", "status": "retired"}),
        _fake_scheme_doc("first", {"scheme": "First"}),
    ]
    manager = mocker.MagicMock(firestore_client=firestore)

    schemes, missing = fetch_schemes_by_ids(
        manager,
        ["first", "second", "retired", "missing", "first"],
    )

    assert [scheme["scheme_id"] for scheme in schemes] == ["first", "second"]
    assert "scraped_text" not in schemes[1]
    assert missing == ["retired", "missing"]
    firestore.get_all.assert_called_once()
    firestore.collection.return_value.document.return_value.get.assert_not_called()
