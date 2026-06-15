"""Unit tests for the vector retrieval step (SearchModel.search).

Behaviour under test: retrieval asks Firestore for the real cosine distance and
turns a closer match into a higher relevance score. Firestore is mocked so no
live index is needed.
"""

import pytest
from search.retriever import RETRIEVAL_LIMIT, SearchModel


def _fake_doc(doc_id, distance):
    class _Doc:
        id = doc_id

        def to_dict(self):
            return {"vector_distance": distance}

    return _Doc()


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
    distances = dict(zip(merged["scheme_id"], merged["vector_distance"]))

    assert scores["near"] > scores["far"]
    assert distances == {"near": 0.1, "far": 0.9}


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
