"""Tests for the feedback endpoint."""

import json
from datetime import datetime, timezone

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


def test_feedback_successful_submission(mocker, mock_request, mock_https_response, mock_auth, mock_firebase_manager):
    """Test successful feedback submission."""
    # Mock the FirebaseManager
    mocker.patch("feedback.feedback.firebase_manager", mock_firebase_manager)

    # Test data
    feedback_data = {
        "feedbackText": "Test feedback",
        "userName": "Test User",
        "userEmail": "test@example.com",
    }

    request = mock_request(method="POST", json_data=feedback_data)

    response = feedback(request)

    # Verify response
    assert response.status_code == 200
    assert json.loads(response.get_data())["success"] is True
    assert "Feedback successfully added" in json.loads(response.get_data())["message"]

    # Verify Firebase interaction
    mock_firebase_manager.firestore_client.collection.assert_called_once_with("userFeedback")
    mock_firebase_manager.firestore_client.collection().add.assert_called_once()
