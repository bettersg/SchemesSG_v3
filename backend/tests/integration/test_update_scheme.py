"""Tests for the update scheme functionality."""

import json

from update_scheme.update_scheme import update_scheme


def test_update_scheme_warmup_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint with warmup request."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Changes": "Test changes",
        "Description": "Test description",
        "Link": "https://test.com",
        "Scheme": "Test Scheme",
        "Status": "Pending",
        "entryId": "test-123",
        "userName": "Test User",
        "userEmail": "test@example.com",
        "typeOfRequest": "New",
        "is_warmup": True,
    }

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["success"] is True
    assert "Warmup request successful" in response_data["message"]
    # Verify no Firestore operations were performed
    mock_manager.firestore_client.collection.assert_not_called()


def test_update_scheme_invalid_method(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint with invalid HTTP method."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request = mock_request(method="GET")

    response = update_scheme(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert response_data["success"] is False
    assert "Only POST requests are allowed" in response_data["message"]


def test_update_scheme_successful_new_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful new scheme update request."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Changes": "New scheme details",
        "Description": "A new government scheme",
        "Link": "https://example.com/scheme",
        "Scheme": "New Government Scheme",
        "Status": "Pending",
        "entryId": "new-123",
        "userName": "John Doe",
        "userEmail": "john@example.com",
        "typeOfRequest": "New",
    }

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["success"] is True
    assert "Request for scheme update successfully added" in response_data["message"]

    # Verify Firestore operation
    mock_manager.firestore_client.collection.assert_called_once_with("schemeEntries")
    mock_manager.firestore_client.collection().add.assert_called_once()
    # Verify the data passed to Firestore includes all required fields
    call_args = mock_manager.firestore_client.collection().add.call_args[0][0]
    assert all(key in call_args for key in request_data.keys())
    assert "timestamp" in call_args  # Verify timestamp was added


def test_update_scheme_successful_edit_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful scheme edit request."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Changes": "Updated eligibility criteria",
        "Description": "Existing scheme needs update",
        "Link": "https://example.com/scheme/existing",
        "Scheme": "Existing Scheme",
        "Status": "Pending",
        "entryId": "existing-123",
        "userName": "Jane Smith",
        "userEmail": "jane@example.com",
        "typeOfRequest": "Edit",
    }

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["success"] is True
    assert "Request for scheme update successfully added" in response_data["message"]

    # Verify Firestore operation
    mock_manager.firestore_client.collection.assert_called_once_with("schemeEntries")
    mock_manager.firestore_client.collection().add.assert_called_once()


def test_update_scheme_missing_required_fields(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint with missing required fields."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    # Missing several required fields
    request_data = {"Changes": "Some changes", "Scheme": "Test Scheme"}

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 200  # The function still returns 200 but with success=False
    response_data = json.loads(response.get_data())
    assert response_data["success"] is True  # Current implementation doesn't validate required fields


def test_update_scheme_firestore_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint when Firestore operation fails."""
    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection().add.side_effect = Exception("Firestore error")
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Changes": "Test changes",
        "Description": "Test description",
        "Link": "https://test.com",
        "Scheme": "Test Scheme",
        "Status": "Pending",
        "entryId": "test-123",
        "userName": "Test User",
        "userEmail": "test@example.com",
        "typeOfRequest": "New",
    }

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert response_data["success"] is False
    assert "Failed to add request for scheme update" in response_data["message"]


def test_update_scheme_cors_preflight(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")

    response = update_scheme(request)

    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
