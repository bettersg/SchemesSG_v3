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


def test_feedback_missing_required_fields(mock_request, mock_https_response, mock_auth):
    """Test feedback endpoint with missing required fields."""
    request = mock_request(method="POST", json_data={})

    response = feedback(request)

    assert response.status_code == 400
    assert json.loads(response.get_data())["success"] is False
    assert "Missing required fields" in json.loads(response.get_data())["message"]


def test_feedback_successful_submission(
    mocker,
    mock_request,
    mock_https_response,
    mock_auth,
    fake_firebase_manager,
    fake_firestore,
):
    mocker.patch("feedback.feedback.create_firebase_manager", return_value=fake_firebase_manager)
    feedback_data = {
        "feedbackText": "Test feedback",
        "userName": "Test User",
        "userEmail": "test@example.com",
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
            json_data={"feedbackText": "Cannot save this", "userEmail": "test@example.com"},
        )
    )

    assert response.status_code == 500
    assert json.loads(response.get_data()) == {
        "success": False,
        "message": "Failed to add feedback",
    }
    assert fake_firestore.list_documents("userFeedback") == {}
