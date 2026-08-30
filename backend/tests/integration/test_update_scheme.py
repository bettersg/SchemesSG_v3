"""Tests for the update scheme functionality."""

import json

from update_scheme.update_scheme import update_scheme


def test_update_scheme_warmup_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test update scheme endpoint with warmup request."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=mock_manager)

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
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET")

    response = update_scheme(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert response_data["success"] is False
    assert "Only POST requests are allowed" in response_data["message"]


def test_update_scheme_successful_new_request(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)
    mocker.patch("update_scheme.update_scheme.is_local_dev", return_value=False)

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
    stored = fake_firestore.get_document("schemeEntries", response_data["docId"])
    assert stored["Scheme"] == "New Government Scheme"
    assert stored["Link"] == "https://example.com/scheme"
    assert stored["typeOfRequest"] == "New"


def test_update_scheme_successful_edit_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful scheme edit request."""
    mock_manager = mocker.MagicMock()
    mock_doc_ref = mocker.MagicMock()
    mock_doc_ref.id = "test-doc-id"
    mock_manager.firestore_client.collection().add.return_value = (mocker.MagicMock(), mock_doc_ref)
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=mock_manager)

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


def test_contribution_rejects_missing_name_and_link(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    """A contribution must identify the scheme and its public page."""
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)

    request_data = {"typeOfRequest": "New", "Scheme": "  ", "Link": ""}

    request = mock_request(method="POST", json_data=request_data)

    response = update_scheme(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert response_data == {
        "success": False,
        "message": "Scheme and Link are required when typeOfRequest is 'new'",
    }
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_contribution_rejects_non_http_url(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data={
                "typeOfRequest": "New",
                "Scheme": "Test Scheme",
                "Link": "javascript:alert(1)",
            },
        )
    )

    assert response.status_code == 400
    assert json.loads(response.get_data()) == {
        "success": False,
        "message": "Link must be a valid http(s) URL",
    }
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_update_scheme_firestore_error(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.fail_writes_for.add("schemeEntries")
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)

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
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=mock_manager)

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
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
):
    """typeOfRequest=update with unknown targetSchemeId -> 400."""
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)

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
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    """typeOfRequest=update with valid target persists targetSchemeId on entry row."""
    fake_firestore.seed("schemes", "scheme-abc", {"scheme": "Existing Scheme"})
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=fake_firebase_manager)
    mocker.patch("update_scheme.update_scheme.is_local_dev", return_value=False)

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
    persisted = fake_firestore.get_document("schemeEntries", body["docId"])
    assert persisted["targetSchemeId"] == "scheme-abc"
    assert persisted["oldLink"] == "https://old-dead-url.example/"


def test_update_scheme_update_type_non_string_target_rejected(
    mock_request, mock_https_response, mock_auth, mocker
):
    """typeOfRequest=update with non-string targetSchemeId -> 400."""
    mock_manager = mocker.MagicMock()
    mocker.patch("update_scheme.update_scheme.create_firebase_manager", return_value=mock_manager)

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
