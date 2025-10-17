"""Unit tests for updated SearchModel."""

import pandas as pd
import pytest
from ml_logic import PaginatedSearchParams, PredictParams, SearchModel


@pytest.fixture(autouse=True)
def reset_search_model():
    """Reset SearchModel singleton state before each test."""
    SearchModel._instance = None
    SearchModel.initialised = False
    SearchModel.query_cache = {}
    yield


@pytest.fixture
def mock_firebase_manager(mocker):
    """Create a fake FirebaseManager with Firestore client mocks."""
    mock_firestore = mocker.MagicMock()
    mock_firebase = mocker.MagicMock()
    mock_firebase.firestore_client = mock_firestore
    return mock_firebase


def test_search_model_initialization(mock_firebase_manager, mocker):
    """Ensure SearchModel initializes with embeddings and index."""
    # Patch inside searchModelManager (correct import path)
    mock_embeddings = mocker.patch("ml_logic.searchModelManager.AzureOpenAIEmbeddings", autospec=True)
    mock_chroma_client = mocker.patch("ml_logic.searchModelManager.chromadb.PersistentClient", autospec=True)
    mock_collection = mocker.MagicMock()
    mock_chroma_client.return_value.get_collection.return_value = mock_collection

    model = SearchModel(mock_firebase_manager)

    mock_embeddings.assert_called_once()
    mock_chroma_client.assert_called_once()
    assert model.firebase_manager == mock_firebase_manager
    assert SearchModel.index == mock_collection
    assert SearchModel.initialised


def test_search_method_success(mocker, mock_firebase_manager):
    """Test the vector search and Firestore fetch process."""
    model = SearchModel(mock_firebase_manager)

    # Mock embeddings output
    mock_embedder = mocker.patch.object(SearchModel, "embeddings")
    mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

    # Mock Chroma index results
    mock_index = mocker.patch.object(SearchModel, "index")
    mock_index.query.return_value = {
        "distances": [[0.1, 0.3]],
        "ids": [["scheme1", "scheme2"]],
    }

    # Mock fetch_schemes_batch
    schemes = [
        {"scheme_id": "scheme1", "search_booster": "Housing support grant"},
        {"scheme_id": "scheme2", "search_booster": "Education bursary"},
    ]
    mocker.patch.object(model, "fetch_schemes_batch", return_value=schemes)

    df = model.search("housing grant", top_k=2)

    assert isinstance(df, pd.DataFrame)
    assert "scheme_id" in df.columns
    assert "vec_similarity_score" in df.columns
    assert all(df["scheme_id"].isin(["scheme1", "scheme2"]))
    assert (df["query"] == "housing grant").all()


def test_rank_method_combines_scores(mocker, mock_firebase_manager):
    """Ensure rank() produces valid combined_scores column."""
    model = SearchModel(mock_firebase_manager)

    data = pd.DataFrame(
        {
            "scheme_id": ["s1", "s2"],
            "search_booster": ["Education support", "Housing grant"],
            "vec_similarity_score": [0.8, 0.5],
        }
    )

    mock_retriever = mocker.patch("ml_logic.searchModelManager.BM25Retriever.from_documents")
    retriever_instance = mocker.MagicMock()
    retriever_instance.k = 2
    retriever_instance.get_relevant_documents.return_value = [
        mocker.MagicMock(metadata={"id": "s1"}),
        mocker.MagicMock(metadata={"id": "s2"}),
    ]
    mock_retriever.return_value = retriever_instance

    ranked = model.rank("education", data)

    assert "bm25_score" in ranked.columns
    assert "combined_scores" in ranked.columns
    assert ranked["combined_scores"].max() <= 1.0


def test_aggregate_and_rank_results_caching(mocker, mock_firebase_manager):
    """Test that results are cached and reused."""
    model = SearchModel(mock_firebase_manager)
    mock_search = mocker.patch.object(model, "search")
    mock_rank = mocker.patch.object(model, "rank")

    mock_search.return_value = pd.DataFrame(
        {"scheme_id": ["1"], "vec_similarity_score": [1.0], "search_booster": ["abc"]}
    )
    mock_rank.return_value = pd.DataFrame({"scheme_id": ["1"], "combined_scores": [0.9]})

    # First call populates cache
    res1 = model.aggregate_and_rank_results("abc", 5, None)
    assert not res1.empty

    # Second call uses cache (search/rank not re-invoked)
    res2 = model.aggregate_and_rank_results("abc", 5, None)
    mock_search.assert_called_once()
    mock_rank.assert_called_once()
    assert res2.equals(res1)


def test_predict_method_saves_to_firestore(mocker, mock_firebase_manager):
    """Test predict() returns session and triggers Firestore save."""
    model = SearchModel(mock_firebase_manager)

    # Mock aggregate_and_rank_results
    mock_df = pd.DataFrame(
        {
            "scheme_id": ["s1", "s2"],
            "combined_scores": [0.8, 0.7],
            "query": ["education", "education"],
        }
    )
    mocker.patch.object(model, "aggregate_and_rank_results", return_value=mock_df)

    save_mock = mocker.patch.object(model, "save_user_query")

    params = PredictParams(query="education")
    result = model.predict(params)

    assert "sessionID" in result
    assert "data" in result
    assert len(result["data"]) == 2
    save_mock.assert_called_once()


def test_predict_method_skips_firestore_on_warmup(mocker, mock_firebase_manager):
    """Warmup calls must skip Firestore save."""
    model = SearchModel(mock_firebase_manager)
    mocker.patch.object(model, "aggregate_and_rank_results", return_value=pd.DataFrame())
    save_mock = mocker.patch.object(model, "save_user_query")
    params = PredictParams(query="ping", is_warmup=True)

    model.predict(params)
    save_mock.assert_not_called()


def test_predict_paginated_basic_flow(mocker, mock_firebase_manager):
    """Test predict_paginated basic behavior."""
    model = SearchModel(mock_firebase_manager)

    # Mock dependencies
    mock_agg = mocker.patch.object(model, "aggregate_and_rank_results")
    mock_agg.return_value = pd.DataFrame({"scheme_id": ["a"], "combined_scores": [0.5], "query": ["q"]})
    mock_save = mocker.patch.object(model, "save_user_query")
    mock_pagination = mocker.patch("ml_logic.searchModelManager.get_paginated_results")
    mock_pagination.return_value = ([{"scheme_id": "a"}], "next123", False, 1)

    params = PaginatedSearchParams(query="grant", limit=1)
    result = model.predict_paginated(params)

    assert "sessionID" in result
    assert "data" in result
    assert "next_cursor" in result
    assert isinstance(result["data"], list)
    mock_save.assert_called_once()
