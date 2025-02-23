"""Tests for the chat functionality."""

import json
import pytest
from chat.chat import chat_message, create_chatbot, Chatbot


def test_chat_warmup_request(mock_request, mock_https_response, mock_auth):
    """Test chat endpoint with warmup request."""
    request = mock_request(method="POST", json_data={"is_warmup": True})

    response = chat_message(request)

    assert response.status_code == 200
    assert "Warmup request successful" in json.loads(response.get_data())["message"]


def test_chat_invalid_method(mock_request, mock_https_response, mock_auth):
    """Test chat endpoint with invalid HTTP method."""
    request = mock_request(method="GET")

    response = chat_message(request)

    assert response.status_code == 405
    assert "Invalid request method; only POST or GET is supported" in json.loads(response.get_data())["error"]


def test_chat_missing_session_id(mock_request, mock_https_response, mock_auth):
    """Test chat endpoint with missing session ID."""
    request = mock_request(method="POST", json_data={"message": "test message"})

    response = chat_message(request)

    assert response.status_code == 404
    assert "Search query with sessionID does not exist" in json.loads(response.get_data())["error"]


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_chatbot_response(mocker, mock_firebase_manager):
    """Test chatbot response generation.

    Note: This test is skipped by default as it requires OpenAI API key.
    To run this test, ensure you have the necessary API key and remove the skip decorator.
    """
    # Mock the Chatbot
    mock_chatbot = mocker.MagicMock()
    mocker.patch.object(Chatbot, "_instance", mock_chatbot)
    mocker.patch.object(Chatbot, "initialised", True)
    mocker.patch("chat.chat.FirebaseManager", return_value=mock_firebase_manager)

    # Test data
    top_schemes_text = "Test scheme description"
    input_text = "What is this scheme about?"
    session_id = "test-session"
    query_text = "test query"

    # Mock response
    expected_response = {
        "response": "This is a test scheme that helps with testing.",
        "success": True,
    }
    mock_chatbot.chatbot.return_value = expected_response

    # Get chatbot instance
    chatbot = create_chatbot()

    # Test chat response
    result = chatbot.chatbot(
        top_schemes_text=top_schemes_text,
        input_text=input_text,
        session_id=session_id,
        query_text=query_text,
    )

    assert result == expected_response
    mock_chatbot.chatbot.assert_called_once_with(
        top_schemes_text=top_schemes_text,
        input_text=input_text,
        session_id=session_id,
        query_text=query_text,
    )
