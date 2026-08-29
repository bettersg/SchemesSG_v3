"""Tests for the search functionality with pagination."""

import json

import pytest
from schemes.search import create_search_model, schemes_search


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


def test_search_invalid_pagination_value_returns_bad_request(
    mock_search_model, mock_request, mock_verify_auth
):
    request = mock_request(
        method="POST",
        json_data={"query": "education", "limit": "not-a-number"},
    )

    response = schemes_search(request)

    assert response.status_code == 400
    assert json.loads(response.get_data(as_text=True)) == {
        "error": "Invalid request body"
    }


def test_search_valid_request(mock_search_model, mock_request, mock_verify_auth):
    """Test a valid paginated search request."""
    mock_results = {
        "sessionID": "test-session",
        "data": [
            {"scheme_id": "scheme-1", "scheme_name": "Test Scheme 1"},
            {"scheme_id": "scheme-2", "scheme_name": "Test Scheme 2"},
        ],
        "total_count": 10,
        "next_cursor": "test-cursor",
        "has_more": True,
    }
    mock_search_model.predict_paginated.return_value = mock_results

    req = mock_request(
        method="POST",
        json_data={
            "query": "education",
            "limit": 2,
            "top_k": 50,
            "similarity_threshold": 0,
        },
        headers={
            "Content-Type": "application/json",
            "Origin": "https://schemes.sg",
        },
    )

    response = schemes_search(req)

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.headers["Access-Control-Allow-Origin"] == "https://schemes.sg"
    assert json.loads(response.get_data(as_text=True)) == mock_results


def test_search_empty_results_contract(
    mock_search_model, mock_request, mock_verify_auth
):
    mock_search_model.predict_paginated.return_value = {
        "sessionID": "empty-session",
        "data": [],
        "total_count": 0,
        "next_cursor": None,
        "has_more": False,
    }
    request = mock_request(method="POST", json_data={"query": "no matches"})

    response = schemes_search(request)

    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True)) == {
        "sessionID": "empty-session",
        "data": [],
        "total_count": 0,
        "next_cursor": None,
        "has_more": False,
    }


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
