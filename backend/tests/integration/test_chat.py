"""Tests for the chat functionality."""

import json

import pytest
from chat.chat import Chatbot, chat_message, create_chatbot


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


def test_chat_authentication_failure(mock_request, mock_https_response, mocker):
    """Test chat endpoint with authentication failure."""
    # Mock authentication to fail
    mocker.patch("chat.chat.verify_auth_token", return_value=(False, "Invalid token"))

    request = mock_request(method="POST", json_data={"message": "test", "sessionID": "test-session"})

    response = chat_message(request)

    assert response.status_code == 401
    assert "Authentication failed: Invalid token" in json.loads(response.get_data())["error"]


def test_chat_invalid_json(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat endpoint with invalid JSON."""
    request = mock_request(method="POST", json_data={"sessionID": "test"})  # Valid sessionID to pass that check
    mocker.patch.object(request, "get_json", side_effect=Exception("Invalid JSON"))

    response = chat_message(request)

    assert response.status_code == 400
    assert "Invalid request body" in json.loads(response.get_data())["error"]


def test_chat_firestore_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat endpoint when Firestore query fails."""
    # Mock create_chatbot and firestore client
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Make firestore query raise an exception
    mock_firestore.collection().document().get.side_effect = Exception("Firestore error")

    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(method="POST", json_data={"message": "test", "sessionID": "test-session"})

    response = chat_message(request)

    assert response.status_code == 500
    assert (
        "Internal server error, unable to fetch user query from firestore" in json.loads(response.get_data())["error"]
    )


def test_chat_session_processing_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat endpoint when session data processing fails."""
    # Mock create_chatbot and firestore client
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document exists but has invalid data structure
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.side_effect = Exception("Invalid data structure")
    mock_firestore.collection().document().get.return_value = mock_doc

    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(method="POST", json_data={"message": "test", "sessionID": "test-session"})

    response = chat_message(request)

    assert response.status_code == 500
    assert "Error processing session data" in json.loads(response.get_data())["error"]


def test_chat_successful_response(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful chat response."""
    # Mock create_chatbot
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document with valid data
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query_text": "test query",
        "schemes_response": [{"agency": "MOH", "planning_area": "Central", "scheme_name": "Test Scheme"}],
    }
    mock_firestore.collection().document().get.return_value = mock_doc

    # Mock chatbot response
    mock_chatbot.chatbot.return_value = {"response": True, "message": "Test response"}

    # Mock dataframe_to_text
    mocker.patch("chat.chat.dataframe_to_text", return_value="Test schemes text")

    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(method="POST", json_data={"message": "test", "sessionID": "test-session"})

    response = chat_message(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["response"] is True
    assert response_data["message"] == "Test response"


def test_chat_with_agency_filter(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat with agency filtering."""
    # Mock create_chatbot
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document with multiple agencies
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query_text": "test query",
        "schemes_response": [
            {"agency": "MOH", "planning_area": "Central", "scheme_name": "Health Scheme"},
            {"agency": "MOE", "planning_area": "North", "scheme_name": "Education Scheme"},
        ],
    }
    mock_firestore.collection().document().get.return_value = mock_doc

    # Mock chatbot response
    mock_chatbot.chatbot.return_value = {"response": True, "message": "Filtered response"}

    # Mock dataframe_to_text to capture the filtered dataframe
    def mock_dataframe_to_text(df):
        # Verify filtering worked - should only have MOH agency
        assert len(df) == 1
        assert df.iloc[0]["agency"] == "MOH"
        return "Filtered schemes text"

    mocker.patch("chat.chat.dataframe_to_text", side_effect=mock_dataframe_to_text)
    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(
        method="POST",
        json_data={
            "message": "test",
            "sessionID": "test-session",
            "agency": ["MOH"],  # Filter by MOH agency
        },
    )

    response = chat_message(request)

    assert response.status_code == 200


def test_chat_with_planning_area_filter(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat with planning area filtering."""
    # Mock create_chatbot
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document with multiple planning areas
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query_text": "test query",
        "schemes_response": [
            {"agency": "MOH", "planning_area": "Central", "scheme_name": "Central Scheme"},
            {"agency": "MOE", "planning_area": "North", "scheme_name": "North Scheme"},
        ],
    }
    mock_firestore.collection().document().get.return_value = mock_doc

    # Mock chatbot response
    mock_chatbot.chatbot.return_value = {"response": True, "message": "Filtered response"}

    # Mock dataframe_to_text to capture the filtered dataframe
    def mock_dataframe_to_text(df):
        # Verify filtering worked - should only have Central planning area
        assert len(df) == 1
        assert df.iloc[0]["planning_area"] == "Central"
        return "Filtered schemes text"

    mocker.patch("chat.chat.dataframe_to_text", side_effect=mock_dataframe_to_text)
    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(
        method="POST",
        json_data={
            "message": "test",
            "sessionID": "test-session",
            "planning_area": ["Central"],  # Filter by Central planning area
        },
    )

    response = chat_message(request)

    assert response.status_code == 200


def test_chat_streaming_response(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat with streaming enabled."""
    # Mock create_chatbot
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document with valid data
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query_text": "test query",
        "schemes_response": [{"agency": "MOH", "planning_area": "Central", "scheme_name": "Test Scheme"}],
    }
    mock_firestore.collection().document().get.return_value = mock_doc

    # Mock chatbot streaming response
    mock_chatbot.chatbot_stream.return_value = iter(["Hello", " ", "World"])

    mocker.patch("chat.chat.dataframe_to_text", return_value="Test schemes text")
    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(
        method="POST",
        json_data={
            "message": "test",
            "sessionID": "test-session",
            "stream": True,  # Enable streaming
        },
    )

    response = chat_message(request)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "text/event-stream" in response.headers.get("Content-Type", "")


def test_chat_chatbot_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test chat when chatbot execution fails."""
    # Mock create_chatbot
    mock_chatbot = mocker.MagicMock()
    mock_firestore = mocker.MagicMock()
    mock_chatbot.firebase_manager.firestore_client = mock_firestore

    # Mock document with valid data
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "query_text": "test query",
        "schemes_response": [{"agency": "MOH", "planning_area": "Central", "scheme_name": "Test Scheme"}],
    }
    mock_firestore.collection().document().get.return_value = mock_doc

    # Make chatbot raise an exception
    mock_chatbot.chatbot.side_effect = Exception("Chatbot error")

    mocker.patch("chat.chat.dataframe_to_text", return_value="Test schemes text")
    mocker.patch("chat.chat.create_chatbot", return_value=mock_chatbot)

    request = mock_request(method="POST", json_data={"message": "test", "sessionID": "test-session"})

    response = chat_message(request)

    assert response.status_code == 500
    assert "Internal server error" in json.loads(response.get_data())["error"]


def test_chat_options_request(mock_request, mock_https_response):
    """Test chat endpoint with OPTIONS request (CORS preflight)."""
    request = mock_request(method="OPTIONS")

    # Mock handle_cors_preflight
    import chat.chat

    original_handle_cors_preflight = chat.chat.handle_cors_preflight

    def mock_handle_cors_preflight(req):
        from firebase_functions import https_fn

        return https_fn.Response(status=200, headers={"Access-Control-Allow-Origin": "*"})

    chat.chat.handle_cors_preflight = mock_handle_cors_preflight

    try:
        response = chat_message(request)
        assert response.status_code == 200
    finally:
        # Restore original function
        chat.chat.handle_cors_preflight = original_handle_cors_preflight


def test_create_chatbot_already_initialised(mocker):
    """Test create_chatbot when Chatbot is already initialised."""
    # Set chatbot as already initialised
    mock_instance = mocker.MagicMock()
    Chatbot.initialised = True
    Chatbot._instance = mock_instance

    result = create_chatbot()

    assert result == mock_instance


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
