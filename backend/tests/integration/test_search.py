"""Tests for the search functionality."""

import json
import pytest
from schemes.search import schemes_search, create_search_model
from ml_logic import PredictParams


def test_search_warmup_request(mock_request, mock_https_response, mocker):
    """Test search endpoint with warmup request."""
    # Mock the SearchModel to avoid initialization
    mock_model = mocker.MagicMock()
    mock_model.return_value.predict.return_value = {
        "success": True,
        "message": "Warmup request successful",
    }
    mocker.patch("schemes.search.SearchModel", mock_model)

    request = mock_request(
        method="POST", json_data={"is_warmup": True, "query": "test"}
    )

    response = schemes_search(request)

    assert response.status_code == 200
    assert json.loads(response.get_data())["success"] is True
    assert "Warmup request successful" in json.loads(response.get_data())["message"]


def test_search_invalid_method(mock_request, mock_https_response, mocker):
    """Test search endpoint with invalid HTTP method."""
    # Mock the SearchModel to avoid initialization
    mock_model = mocker.MagicMock()
    mocker.patch("schemes.search.SearchModel", mock_model)

    request = mock_request(method="GET")

    response = schemes_search(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert "Invalid request method; only POST is supported" == response_data["error"]


def test_search_missing_query(mock_request, mock_https_response, mocker):
    """Test search endpoint with missing query."""
    # Mock the SearchModel to avoid initialization
    mock_model = mocker.MagicMock()
    mocker.patch("schemes.search.SearchModel", mock_model)

    request = mock_request(method="POST", json_data={})

    response = schemes_search(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Parameter 'query' in body is required" == response_data["error"]


def test_search_successful_query(mock_request, mock_https_response, mocker):
    """Test successful search query."""
    # Mock the SearchModel
    mock_model = mocker.MagicMock()
    expected_results = {
        "success": True,
        "schemes": [
            {"id": 1, "title": "Test Scheme", "description": "Test Description"}
        ],
    }
    mock_model.return_value.predict.return_value = expected_results
    mocker.patch("schemes.search.SearchModel", mock_model)

    request = mock_request(method="POST", json_data={"query": "test query"})

    response = schemes_search(request)

    assert response.status_code == 200
    assert json.loads(response.get_data()) == expected_results


def test_search_with_cors_preflight(mock_request, mock_https_response, mocker):
    """Test search endpoint CORS preflight request."""
    request = mock_request(
        method="OPTIONS", headers={"Origin": "http://localhost:3000"}
    )

    response = schemes_search(request)

    assert response.status_code == 204
    assert (
        response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    )


def test_search_with_prediction_error(mock_request, mock_https_response, mocker):
    """Test search endpoint when prediction fails."""
    # Mock the SearchModel to raise an exception
    mock_model = mocker.MagicMock()
    mock_model.return_value.predict.side_effect = Exception("Prediction failed")
    mocker.patch("schemes.search.SearchModel", mock_model)

    request = mock_request(method="POST", json_data={"query": "test query"})

    response = schemes_search(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert "Internal server error" == response_data["error"]


def test_create_search_model(mock_firebase_manager, mocker):
    """Test creation of search model."""
    # Mock the SearchModel class
    mock_search_model = mocker.MagicMock()
    mock_search_model.return_value.firebase_manager = mock_firebase_manager
    mocker.patch("schemes.search.SearchModel", mock_search_model)
    mocker.patch("schemes.search.FirebaseManager", return_value=mock_firebase_manager)

    model = create_search_model()

    assert model is not None
    assert model.firebase_manager == mock_firebase_manager


@pytest.mark.skip(reason="Requires ML model files")
def test_search_model_prediction(mocker, mock_firebase_manager):
    """Test search model prediction.

    Note: This test is skipped by default as it requires ML model files.
    To run this test, ensure you have the necessary model files and remove the skip decorator.
    """
    # Mock the SearchModel
    mock_search_model = mocker.MagicMock()
    mocker.patch("schemes.search.SearchModel", return_value=mock_search_model)

    # Test prediction
    params = PredictParams(query="test query")
    mock_search_model.predict.return_value = {
        "success": True,
        "schemes": [{"id": 1, "title": "Test Scheme"}],
    }

    model = create_search_model()
    result = model.predict(params)

    assert result["success"] is True
    assert len(result["schemes"]) > 0
    assert result["schemes"][0]["title"] == "Test Scheme"
