"""Tests for the search functionality with pagination."""

import json
import pytest
from schemes.search import schemes_search, create_search_model
from ml_logic import PaginatedSearchParams, SearchModel


@pytest.fixture
def mock_search_model(mocker):
    """Mock SearchModel for testing."""
    mock = mocker.MagicMock()
    mocker.patch("schemes.search.create_search_model", return_value=mock)
    return mock


@pytest.fixture
def mock_verify_auth(monkeypatch):
    """Mock the auth verification function to always succeed."""
    def mock_auth(req):
        return True, "test-user"
    
    # Directly patch the module-level function
    monkeypatch.setattr("schemes.search.verify_auth_token", mock_auth)
    return mock_auth


def test_search_method_not_allowed(mock_search_model, mock_request, mock_verify_auth):
    """Test that non-POST methods are rejected."""
    # Create a GET request
    req = mock_request(method="GET")
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status
    assert response.status_code == 405
    assert "Invalid request method" in response.get_data(as_text=True)


def test_search_invalid_body(mock_search_model, mock_request, mock_verify_auth):
    """Test handling of invalid request body."""
    # Create a POST request with no body
    req = mock_request(method="POST")
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status
    assert response.status_code == 400
    assert "Parameter 'query' in body is required" in response.get_data(as_text=True)


def test_search_missing_query(mock_search_model, mock_request, mock_verify_auth):
    """Test handling of missing query parameter."""
    # Create a POST request with a body but no query
    req = mock_request(
        method="POST",
        json_data={"limit": 10},
        headers={"Content-Type": "application/json"},
    )
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status
    assert response.status_code == 400
    assert "Parameter 'query' in body is required" in response.get_data(as_text=True)


def test_search_valid_request(mock_search_model, mock_request, mock_verify_auth):
    """Test a valid paginated search request."""
    # Create mock search results
    mock_results = {
        "sessionID": "test-session",
        "results": [
            {"id": "scheme-1", "title": "Test Scheme 1", "Similarity": 0.9},
            {"id": "scheme-2", "title": "Test Scheme 2", "Similarity": 0.8},
        ],
        "total_count": 10,
        "next_cursor": "test-cursor",
        "has_more": True,
    }
    mock_search_model.predict_paginated.return_value = mock_results
    
    # Create a valid POST request
    req = mock_request(
        method="POST",
        json_data={
            "query": "education",
            "limit": 2,
            "top_k": 50,
            "similarity_threshold": 0,
        },
        headers={"Content-Type": "application/json"},
    )
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status and content
    assert response.status_code == 200
    
    # Parse response data
    response_data = json.loads(response.get_data(as_text=True))
    
    # Verify structure and content
    assert "sessionID" in response_data
    assert "results" in response_data
    assert "total_count" in response_data
    assert "next_cursor" in response_data
    assert "has_more" in response_data
    
    assert response_data["total_count"] == 10
    assert len(response_data["results"]) == 2
    assert response_data["next_cursor"] == "test-cursor"
    assert response_data["has_more"] is True
    
    # Verify the predict_paginated method was called with the right parameters
    mock_search_model.predict_paginated.assert_called_once()
    call_args = mock_search_model.predict_paginated.call_args[0][0]
    assert isinstance(call_args, PaginatedSearchParams)
    assert call_args.query == "education"
    assert call_args.limit == 2
    assert call_args.top_k == 50
    assert call_args.similarity_threshold == 0


def test_search_auth_failure(mock_search_model, mock_request, monkeypatch):
    """Test authentication failure handling."""
    # Mock auth failure for this specific test
    def mock_auth_fail(req):
        return False, "Auth failed"
    
    # Override the auth verification to fail for this test
    monkeypatch.setattr("schemes.search.verify_auth_token", mock_auth_fail)
    
    # Create a valid POST request
    req = mock_request(
        method="POST",
        json_data={"query": "education"},
        headers={"Content-Type": "application/json"},
    )
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status
    assert response.status_code == 401
    assert "Authentication failed" in response.get_data(as_text=True)


def test_search_server_error(mock_search_model, mock_request, mock_verify_auth):
    """Test server error handling."""
    # Mock predict_paginated to raise an exception
    mock_search_model.predict_paginated.side_effect = Exception("Test error")
    
    # Create a valid POST request
    req = mock_request(
        method="POST",
        json_data={"query": "education"},
        headers={"Content-Type": "application/json"},
    )
    
    # Call the endpoint
    response = schemes_search(req)
    
    # Check response status
    assert response.status_code == 500
    assert "Internal server error" in response.get_data(as_text=True)


def test_search_warmup_request(mock_search_model, mock_request, mock_verify_auth):
    """Test search endpoint with warmup request."""
    # Mock the warmup response
    mock_results = {
        "success": True,
        "message": "Warmup request successful",
    }
    mock_search_model.predict_paginated.return_value = mock_results

    # Create a warmup request
    req = mock_request(
        method="POST", 
        json_data={"is_warmup": True, "query": "test"},
        headers={"Content-Type": "application/json"},
    )

    response = schemes_search(req)

    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data["success"] is True
    assert "Warmup request successful" in response_data["message"]


def test_search_with_cors_preflight(mock_request):
    """Test search endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")

    response = schemes_search(request)

    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") is not None


def test_create_search_model(mock_firebase_manager, mocker):
    """Test creation of search model."""
    # Mock the SearchModel class
    mock_search_model = mocker.MagicMock()
    mocker.patch("schemes.search.SearchModel", mock_search_model)
    mocker.patch("schemes.search.FirebaseManager", return_value=mock_firebase_manager)

    model = create_search_model()

    assert model is not None
    assert mock_search_model.called
