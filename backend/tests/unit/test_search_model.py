"""Unit tests for SearchModel."""

import numpy as np
import pandas as pd
import pytest
import torch
import torch.nn.functional as F
from ml_logic import SearchModel, PredictParams


@pytest.fixture(autouse=True)
def reset_search_model():
    """Reset SearchModel singleton state before each test."""
    SearchModel._instance = None
    SearchModel.initialised = False
    yield


def test_search_model_initialization(mock_firebase_manager):
    """Test SearchModel initialization."""
    model = SearchModel(mock_firebase_manager)
    assert model.firebase_manager == mock_firebase_manager


def test_search_model_predict(mocker, mock_firebase_manager):
    """Test predict method."""
    model = SearchModel(mock_firebase_manager)

    # Valid parameters
    valid_params = PredictParams(query="test query")

    # Mock preprocessor
    model.preprocessor = mocker.MagicMock()
    model.preprocessor.split_query_into_needs.return_value = ["test query"]

    # Create a mock DataFrame with the expected structure
    mock_df = pd.DataFrame(
        {
            "id": [1, 2],
            "title": ["Test Scheme 1", "Test Scheme 2"],
            "Similarity": [0.9, 0.8],
            "query": ["test query", "test query"],
        }
    )

    # Mock combine_and_aggregate_results to return the DataFrame
    model.combine_and_aggregate_results = mocker.MagicMock(return_value=mock_df)

    result = model.predict(valid_params)

    assert "sessionID" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) == 2
    assert result["data"][0]["title"] == "Test Scheme 1"


def test_search_model_search_similar_items(mocker, mock_firebase_manager):
    """Test search_similar_items method."""
    model = SearchModel(mock_firebase_manager)

    # Mock the class attributes to prevent segfault
    model.__class__.tokenizer = mocker.MagicMock()
    model.__class__.model = mocker.MagicMock()
    model.__class__.index = mocker.MagicMock()
    model.__class__.index_to_scheme_id = {"0": "scheme1", "1": "scheme2"}

    # Create real PyTorch tensors for the mock data
    token_embeddings = torch.randn(1, 3, 768)  # Batch size 1, 3 tokens, 768 dimensions
    attention_mask = torch.ones(1, 3)  # Batch size 1, 3 tokens

    # Mock the model output to return the token embeddings
    model_output = mocker.MagicMock()
    model_output.__getitem__.side_effect = (
        lambda x: token_embeddings if x == 0 else None
    )

    # Mock the tokenizer to return the attention mask
    encoded_input = {"attention_mask": attention_mask}
    model.__class__.tokenizer.return_value = encoded_input
    model.__class__.model.return_value = model_output

    # Mock FAISS search results - use numpy arrays
    distances = np.array([[0.1, 0.2]], dtype=np.float32)
    indices = np.array([[0, 1]], dtype=np.int64)
    model.__class__.index.search.return_value = (distances, indices)

    # Mock fetch_schemes_batch
    mock_schemes = [
        {
            "id": "scheme1",
            "title": "Scheme 1",
            "Description": "Test 1",
            "Agency": "Agency 1",
            "Link": "link1",
            "scraped_text": "text1",
            "Scheme": "Scheme 1",  # Add Scheme field as it's required
        },
        {
            "id": "scheme2",
            "title": "Scheme 2",
            "Description": "Test 2",
            "Agency": "Agency 2",
            "Link": "link2",
            "scraped_text": "text2",
            "Scheme": "Scheme 2",  # Add Scheme field as it's required
        },
    ]
    model.fetch_schemes_batch = mocker.MagicMock(return_value=mock_schemes)

    # Mock torch.no_grad context
    no_grad_mock = mocker.patch("torch.no_grad")
    no_grad_mock.return_value.__enter__.return_value = None
    no_grad_mock.return_value.__exit__.return_value = None

    # Mock F.normalize to return a tensor that can be converted to numpy
    normalized_tensor = torch.ones(1, 768)  # Match embedding dimensions
    mocker.patch("torch.nn.functional.normalize", return_value=normalized_tensor)

    results = model.search_similar_items("test query", "original query", 2)

    assert not results.empty
    assert "Similarity" in results.columns
    assert "query" in results.columns
    assert len(results) <= 2  # Should return at most 2 results
    assert "Scheme" in results.columns  # Verify Scheme column exists
