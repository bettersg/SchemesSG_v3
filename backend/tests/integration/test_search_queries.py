"""Tests for the search queries functionality."""

import json
import pytest
from schemes.search_queries import retrieve_search_queries


def test_search_queries_warmup_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint with warmup request."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET", args={"is_warmup": "true"})
    request.path = "/test-session-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert "Warmup request successful" in response_data["message"]


def test_search_queries_invalid_method(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint with invalid HTTP method."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="POST")
    request.path = "/test-session-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert "Invalid request method; only GET is supported" == response_data["error"]


def test_search_queries_missing_session_id(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint with missing session ID."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/"  # No session ID provided

    response = retrieve_search_queries(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Invalid path parameters, please provide session id" == response_data["error"]


def test_search_queries_successful_fetch(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful search queries fetch."""
    # Mock the FirebaseManager and document
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query": "test query",
        "timestamp": "2024-02-06T12:00:00Z",
        "results": ["scheme1", "scheme2"],
    }

    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/test-session-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert "data" in response_data
    assert response_data["data"]["query"] == "test query"
    assert len(response_data["data"]["results"]) == 2


def test_search_queries_not_found(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint when query is not found."""
    # Mock the FirebaseManager and document
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False

    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/non-existent-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 404
    response_data = json.loads(response.get_data())
    assert "Search query with provided session id does not exist" == response_data["error"]


def test_search_queries_firestore_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint when Firestore query fails."""
    # Mock the FirebaseManager to raise an exception
    mock_ref = mocker.MagicMock()
    mock_ref.get.side_effect = Exception("Firestore error")

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.search_queries.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/test-session-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert "Internal server error" in response_data["error"]


def test_search_queries_cors_preflight(mock_request, mock_https_response, mock_auth, mocker):
    """Test search queries endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")
    request.path = "/test-session-id"

    response = retrieve_search_queries(request)

    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
