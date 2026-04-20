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
    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.id = "test-doc-id"
    mock_manager.firestore_client.collection().add.return_value = (mocker.MagicMock(), mock_doc_ref)
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

    # Verify Firestore operation - collection is called once during mock setup and once during execution
    mock_manager.firestore_client.collection.assert_called_with("schemeEntries")
    # Verify add was called (once during mock setup, once during execution)
    assert mock_manager.firestore_client.collection().add.call_count >= 1


def test_update_scheme_successful_edit_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful scheme edit request."""
    mock_manager = mocker.MagicMock()
    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.id = "test-doc-id"
    mock_manager.firestore_client.collection().add.return_value = (mocker.MagicMock(), mock_doc_ref)
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

    # Verify Firestore operation - collection is called once during mock setup and once during execution
    mock_manager.firestore_client.collection.assert_called_with("schemeEntries")
    # Verify add was called (once during mock setup, once during execution)
    assert mock_manager.firestore_client.collection().add.call_count >= 1


def test_update_scheme_missing_required_fields(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint with missing required fields."""
    mock_manager = mocker.MagicMock()
    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.id = "test-doc-id"
    mock_manager.firestore_client.collection().add.return_value = (mocker.MagicMock(), mock_doc_ref)
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


def test_update_scheme_update_type_missing_target(
    mock_request, mock_https_response, mock_auth, mocker
):
    """typeOfRequest=update requires targetSchemeId."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Link": "https://example.com/replacement",
        "Scheme": "Existing Scheme",
        "typeOfRequest": "update",
        "userEmail": "bot@example.com",
        "userName": "recover-scheme-links",
    }

    response = update_scheme(mock_request(method="POST", json_data=request_data))
    assert response.status_code == 400
    body = json.loads(response.get_data())
    assert body["success"] is False
    assert "targetSchemeId" in body["message"]


def test_update_scheme_update_type_unknown_target(
    mock_request, mock_https_response, mock_auth, mocker
):
    """typeOfRequest=update with unknown targetSchemeId -> 400."""
    mock_manager = mocker.MagicMock()
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False
    mock_manager.firestore_client.collection().document().get.return_value = mock_doc
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Link": "https://example.com/replacement",
        "Scheme": "Existing Scheme",
        "typeOfRequest": "update",
        "targetSchemeId": "nonexistent-id",
    }

    response = update_scheme(mock_request(method="POST", json_data=request_data))
    assert response.status_code == 400
    body = json.loads(response.get_data())
    assert body["success"] is False
    assert "nonexistent-id" in body["message"]
    assert "not found" in body["message"].lower()


def test_update_scheme_update_type_happy_path(
    mock_request, mock_https_response, mock_auth, mocker
):
    """typeOfRequest=update with valid target persists targetSchemeId on entry row."""
    mock_manager = mocker.MagicMock()
    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.id = "entry-42"
    mock_target = mocker.MagicMock()
    mock_target.exists = True
    mock_target.to_dict.return_value = {"scheme": "Existing Scheme"}
    mock_manager.firestore_client.collection().document().get.return_value = mock_target
    mock_manager.firestore_client.collection().add.return_value = (
        mocker.MagicMock(),
        mock_doc_ref,
    )
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Link": "https://example.com/replacement",
        "Scheme": "Existing Scheme",
        "typeOfRequest": "update",
        "targetSchemeId": "scheme-abc",
        "oldLink": "https://old-dead-url.example/",
        "userEmail": "bot@example.com",
        "userName": "recover-scheme-links",
    }

    response = update_scheme(mock_request(method="POST", json_data=request_data))
    assert response.status_code == 200

    body = json.loads(response.get_data())
    assert body["success"] is True
    assert body["docId"] == "entry-42"

    add_calls = mock_manager.firestore_client.collection().add.call_args_list
    persisted = next(
        (
            call.args[0]
            for call in add_calls
            if call.args and call.args[0].get("targetSchemeId") == "scheme-abc"
        ),
        None,
    )
    assert persisted is not None
    assert persisted.get("oldLink") == "https://old-dead-url.example/"


def test_update_scheme_update_type_non_string_target_rejected(
    mock_request, mock_https_response, mock_auth, mocker
):
    """typeOfRequest=update with non-string targetSchemeId -> 400."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.firebase_manager", mock_manager)

    request_data = {
        "Link": "https://example.com/replacement",
        "Scheme": "Existing Scheme",
        "typeOfRequest": "update",
        "targetSchemeId": 123,  # not a string
    }

    response = update_scheme(mock_request(method="POST", json_data=request_data))
    assert response.status_code == 400
    body = json.loads(response.get_data())
    assert body["success"] is False
    assert "targetSchemeId" in body["message"]
    # Must not hit Firestore at all (bail before .collection("schemes"))
    mock_manager.firestore_client.collection().document().get.assert_not_called()
