"""Tests for the feedback endpoint."""

import json

import pytest
from feedback.feedback import feedback


def test_feedback_warmup_request(mock_request, mock_https_response, mock_auth):
    """Test feedback endpoint with warmup request."""
    request = mock_request(method="POST", json_data={"is_warmup": True})

    response = feedback(request)

    assert response.status_code == 200
    assert json.loads(response.get_data())["success"] is True
    assert "Warmup request successful" in json.loads(response.get_data())["message"]


def test_feedback_invalid_method(mock_request, mock_https_response, mock_auth):
    """Test feedback endpoint with invalid HTTP method."""
    request = mock_request(method="GET")

    response = feedback(request)

    assert response.status_code == 405
    assert json.loads(response.get_data())["success"] is False
    assert "Only POST requests are allowed" in json.loads(response.get_data())["message"]


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {},
        {"feedbackText": "Missing user and category"},
        {"feedbackText": "Text", "userName": "User", "userEmail": "user@example.com"},
        {"feedbackText": "Text", "userName": "   ", "userEmail": "user@example.com", "feedbackCategory": "General feedback"},
        {"feedbackText": "Text", "userName": "User", "userEmail": "   ", "feedbackCategory": "General feedback"},
        {"feedbackText": "Text", "userName": "User", "userEmail": "user@example.com", "feedbackCategory": "Invalid Category"},
    ],
)
def test_feedback_missing_required_fields(
    invalid_payload,
    mock_request,
    mock_https_response,
    mock_auth,
):
    """Test feedback endpoint with missing or invalid required fields."""
    request = mock_request(method="POST", json_data=invalid_payload)

    response = feedback(request)

    assert response.status_code == 400
    assert json.loads(response.get_data())["success"] is False
    assert "Missing or invalid required fields" in json.loads(response.get_data())["message"]


def test_feedback_successful_submission(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)
    mock_notion = mocker.patch("feedback.feedback.create_notion_feedback", return_value="notion-page-123")
    feedback_data = {
        "feedbackText": "Test feedback",
        "userName": "Test User",
        "userEmail": "test@example.com",
        "feedbackCategory": "Report wrong / missing information",
        "source": "scheme",
        "sentiment": None,
        "schemeId": "child-care-subsidy",
        "schemeName": "Child Care Subsidy",
    }

    request = mock_request(method="POST", json_data=feedback_data)

    response = feedback(request)

    assert response.status_code == 200
    assert json.loads(response.get_data())["success"] is True
    assert "Feedback successfully added" in json.loads(response.get_data())["message"]
    stored = list(fake_firestore.list_documents("userFeedback").values())
    assert len(stored) == 1
    assert stored[0]["feedbackText"] == "Test feedback"
    assert stored[0]["userName"] == "Test User"
    assert stored[0]["userEmail"] == "test@example.com"
    assert stored[0]["feedbackCategory"] == "Report wrong / missing information"
    assert stored[0]["source"] == "scheme"
    assert stored[0]["sentiment"] is None
    assert stored[0]["schemeId"] == "child-care-subsidy"
    assert stored[0]["schemeName"] == "Child Care Subsidy"
    assert stored[0]["notionSyncStatus"] == "synced"
    assert stored[0]["notionPageId"] == "notion-page-123"
    mock_notion.assert_called_once()


def test_feedback_submission_handles_notion_sync_failure(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)
    mocker.patch("feedback.feedback.create_notion_feedback", side_effect=Exception("Notion API error"))
    feedback_data = {
        "feedbackText": "Test feedback",
        "userName": "Test User",
        "userEmail": "test@example.com",
        "feedbackCategory": "General feedback",
    }

    request = mock_request(method="POST", json_data=feedback_data)

    response = feedback(request)

    assert response.status_code == 200
    assert json.loads(response.get_data())["success"] is True
    assert "Feedback successfully added" in json.loads(response.get_data())["message"]
    stored = list(fake_firestore.list_documents("userFeedback").values())
    assert len(stored) == 1
    assert stored[0]["notionSyncStatus"] == "failed"
    assert stored[0]["notionPageId"] is None


@pytest.mark.parametrize("message_index", [True, -1])
def test_chat_rating_rejects_invalid_message_index(
    message_index,
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)
    request = mock_request(
        method="POST",
        json_data={
            "source": "chat",
            "sessionId": "session-1",
            "messageIndex": message_index,
            "rating": "up",
        },
    )

    response = feedback(request)

    assert response.status_code == 400
    assert json.loads(response.get_data()) == {
        "success": False,
        "message": "Invalid rating payload",
    }
    assert fake_firestore.list_documents("chatRatings") == {}


@pytest.mark.parametrize(
    "payload",
    [
        {"source": "chat", "sessionId": "session-1", "rating": "up"},
        {"source": "chat", "sessionId": " ", "messageIndex": 0, "rating": "up"},
        {"source": "chat", "sessionId": 123, "messageIndex": 0, "rating": "up"},
    ],
)
def test_chat_rating_rejects_invalid_session_identity(
    payload,
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)

    response = feedback(mock_request(method="POST", json_data=payload))

    assert response.status_code == 400
    assert json.loads(response.get_data()) == {
        "success": False,
        "message": "Invalid rating payload",
    }
    assert fake_firestore.list_documents("chatRatings") == {}


def test_chat_rating_can_be_recorded_and_changed(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)

    for rating in ("up", "down"):
        response = feedback(
            mock_request(
                method="POST",
                json_data={
                    "source": "chat",
                    "sessionId": "session-1",
                    "messageIndex": 4,
                    "rating": rating,
                },
            )
        )
        assert response.status_code == 200

    stored = fake_firestore.get_document("chatRatings", "session-1")
    assert stored["sessionId"] == "session-1"
    assert stored["ratings"] == {"4": "down"}


def test_chat_rating_can_be_cleared(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)
    payload = {
        "source": "chat",
        "sessionId": "session-1",
        "messageIndex": 4,
        "rating": "up",
    }
    feedback(mock_request(method="POST", json_data=payload))

    response = feedback(mock_request(method="POST", json_data={**payload, "rating": None}))

    assert response.status_code == 200
    stored = fake_firestore.get_document("chatRatings", "session-1")
    assert "4" not in stored["ratings"]


def test_feedback_returns_stable_error_when_firestore_write_fails(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.fail_writes_for.add("userFeedback")
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)

    response = feedback(
        mock_request(
            method="POST",
            json_data={
                "feedbackText": "Cannot save this",
                "userName": "Test User",
                "userEmail": "test@example.com",
                "feedbackCategory": "General feedback",
            },
        )
    )

    assert response.status_code == 500
    assert json.loads(response.get_data()) == {
        "success": False,
        "message": "Failed to add feedback",
    }
    assert fake_firestore.list_documents("userFeedback") == {}


def test_create_notion_feedback(mocker, monkeypatch):
    monkeypatch.setenv("NOTION_FEEDBACK_API_KEY", "test-notion-key")
    monkeypatch.setenv("NOTION_FEEDBACK_DATA_SOURCE_ID", "test-data-source-id")

    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "page-xyz-123"}
    mock_post = mocker.patch("feedback.feedback.requests.post", return_value=mock_response)

    from feedback.feedback import create_notion_feedback

    page_id = create_notion_feedback(
        feedback_id="fb-123",
        feedback_data={
            "userName": "Alice",
            "userEmail": "alice@example.com",
            "feedbackText": "Great app",
            "feedbackCategory": "Suggest a feature",
            "source": "scheme",
            "sentiment": "positive",
            "schemeId": "scheme-1",
            "schemeName": "Scheme One",
        },
    )

    assert page_id == "page-xyz-123"
    mock_post.assert_called_once()
    called_args, called_kwargs = mock_post.call_args
    assert called_args[0] == "https://api.notion.com/v1/pages"
    assert called_kwargs["headers"]["Authorization"] == "Bearer test-notion-key"
    assert called_kwargs["headers"]["Notion-Version"] == "2025-09-03"
    props = called_kwargs["json"]["properties"]
    assert props["Name"]["title"][0]["text"]["content"] == "Alice"
    assert props["Email"]["email"] == "alice@example.com"
    assert props["Feedback category"]["select"]["name"] == "Suggest a feature"
    assert props["Source"]["select"]["name"] == "scheme"
    assert props["Sentiment"]["select"]["name"] == "positive"
    assert props["Scheme ID"]["rich_text"][0]["text"]["content"] == "scheme-1"
    assert props["Scheme Name"]["rich_text"][0]["text"]["content"] == "Scheme One"

