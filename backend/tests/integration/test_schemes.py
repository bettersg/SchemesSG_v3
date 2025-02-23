"""Tests for the schemes functionality."""

import json
import pytest
from schemes.schemes import schemes


def test_schemes_warmup_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint with warmup request."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET", args={"is_warmup": "true"})
    request.path = "/test-scheme-id"

    response = schemes(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert "Warmup request successful" in response_data["message"]


def test_schemes_invalid_method(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint with invalid HTTP method."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="POST")
    request.path = "/test-scheme-id"

    response = schemes(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert "Invalid request method; only GET is supported" == response_data["error"]


def test_schemes_missing_id(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint with missing scheme ID."""
    # Mock the FirebaseManager
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/"  # No scheme ID provided

    response = schemes(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Invalid path parameters, please provide schemes id" == response_data["error"]


def test_schemes_successful_fetch(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful scheme fetch."""
    # Mock the FirebaseManager and document
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "title": "Test Scheme",
        "description": "Test Description",
        "eligibility": ["Test Eligibility"],
    }

    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/test-scheme-id"

    response = schemes(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert "data" in response_data
    assert response_data["data"]["title"] == "Test Scheme"


def test_schemes_not_found(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint when scheme is not found."""
    # Mock the FirebaseManager and document
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False

    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/non-existent-id"

    response = schemes(request)

    assert response.status_code == 404
    response_data = json.loads(response.get_data())
    assert "Scheme with provided id does not exist" == response_data["error"]


def test_schemes_firestore_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint when Firestore query fails."""
    # Mock the FirebaseManager to raise an exception
    mock_ref = mocker.MagicMock()
    mock_ref.get.side_effect = Exception("Firestore error")

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().document.return_value = mock_ref

    mocker.patch("schemes.schemes.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")
    request.path = "/test-scheme-id"

    response = schemes(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert "Internal server error" in response_data["error"]


def test_schemes_cors_preflight(mock_request, mock_https_response, mock_auth, mocker):
    """Test schemes endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")
    request.path = "/test-scheme-id"

    response = schemes(request)

    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
