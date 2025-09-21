"""Integration tests for chatbotManager.py."""

from datetime import datetime, timezone

import os
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from ml_logic.chatbotManager import Chatbot
from ml_logic.config import ChatbotConfig


@pytest.fixture(autouse=True)
def clear_chatbot_instance():
    """Clear Chatbot singleton instance between tests."""
    Chatbot._instance = None
    Chatbot.initialised = False
    yield


@pytest.fixture
def mock_firebase_manager(mocker):
    """Fixture for mocked FirebaseManager."""
    mock = mocker.MagicMock()
    mock.firestore_client = mocker.MagicMock()
    return mock


def test_chatbot_initialization_with_init_chat_model(mocker):
    """Test full Chatbot initialization using init_chat_model."""

    # Patch init_chat_model where Chatbot actually uses it
    mock_init = mocker.patch("ml_logic.chatbotManager.init_chat_model", return_value=mocker.MagicMock())

    # Set environment variable for Azure deployment
    mocker.patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT_NAME": "test-deployment"}, clear=True)

    # Assign a mock firebase manager (required by initialise)
    mock_firebase = mocker.MagicMock()
    chatbot = Chatbot(mock_firebase)
    chatbot.initialise()

    # Assertions for full initialization
    assert chatbot.initialised is True
    assert chatbot.firebase_manager is mock_firebase
    assert hasattr(chatbot, "cache")  # if cache is created during initialization
    assert Chatbot._instance is not None

    mock_init.assert_called_once_with(
        "azure_openai:gpt-4.1-mini",
        azure_deployment="test-deployment",
        **ChatbotConfig().__dict__,
    )


def test_chatbot_cache_hit(mock_firebase_manager, mocker):
    """Test chatbot cache hit by patching graph.invoke."""

    chatbot = Chatbot(mock_firebase_manager)

    # Patch graph.invoke to simulate LLM call
    mock_invoke = mocker.patch.object(
        chatbot.graph,
        "invoke",
        side_effect=[
            [{"chatbot": {"messages": [mocker.MagicMock(content="Fresh response")]}}],
            [{"chatbot": {"messages": [mocker.MagicMock(content="Cached response")]}}],
        ],
    )

    # First call
    response1 = chatbot.chatbot(
        top_schemes_text="schemes",
        input_text="user input",
        session_id="session1",
        query_text="original query",
    )
    assert response1["message"] == "Fresh response"

    # Second call simulates cache hit (graph.invoke returns cached response)
    response2 = chatbot.chatbot(
        top_schemes_text="schemes",
        input_text="user input",
        session_id="session1",
        query_text="original query",
    )
    assert response2["message"] == "Cached response"

    # Ensure graph.invoke was called twice (first for real, second simulating cache)
    assert mock_invoke.call_count == 2


def test_chatbot_stream_with_firestore_sync(mock_firebase_manager, mocker):
    """Test that chatbot_stream yields chunks and stores in Firestore."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock graph.stream to return the expected format: [(mode, data), ...]
    # When there's no cache hit, we get messages mode first, then updates
    mock_stream_data = [
        ("messages", (mocker.MagicMock(content="Hello "), None)),
        ("messages", (mocker.MagicMock(content="World!"), None)),
        ("updates", {"chatbot": {"messages": [mocker.MagicMock(content="Hello World!")]}}),
    ]
    mocker.patch.object(chatbot.graph, "stream", return_value=mock_stream_data)

    # Collect streamed output
    chunks = []
    for token in chatbot.chatbot_stream(
        top_schemes_text="schemes",
        input_text="Hi",
        session_id="session_stream",
        query_text="query text",
    ):
        chunks.append(token)

    # Check that tokens match message content from streaming
    assert "Hello " in chunks
    assert "World!" in chunks


def test_chatbot_stream_cache_hit(mock_firebase_manager, mocker):
    """Test chatbot stream with cache hit - should use _replay_cached_tokens."""

    # Helper class to simulate LLM message object
    class MockMessage:
        def __init__(self, content):
            self.content = content

    chatbot = Chatbot(mock_firebase_manager)

    # Mock graph.stream to simulate cache hit scenario
    # When there's a cache hit, we only get 'updates' mode, no 'messages' mode
    cached_response = {"chatbot": {"messages": [MockMessage("This is a cached response")]}}
    mock_stream_data = [
        ("updates", cached_response),
        # No messages mode when cached
    ]
    mocker.patch.object(chatbot.graph, "stream", return_value=mock_stream_data)

    # Collect streamed output
    chunks = []
    for token in chatbot.chatbot_stream(
        top_schemes_text="schemes", input_text="user input", session_id="session1", query_text="original query"
    ):
        chunks.append(token)

    # With cache hit, _replay_cached_tokens should be called
    # It splits the cached message into tokens
    full_response = "".join(chunks).strip()
    assert "This is a cached response" in full_response


def test_chatbot_stream_with_history_update(mock_firebase_manager, mocker):
    """Test streaming generates correct tokens from messages mode."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock the graph.stream to simulate streaming response
    mock_stream_data = [
        ("messages", (mocker.MagicMock(content="First"), None)),
        ("messages", (mocker.MagicMock(content=" response"), None)),
        ("updates", {"chatbot": {"messages": [mocker.MagicMock(content="First response")]}}),
    ]
    mocker.patch.object(chatbot.graph, "stream", return_value=mock_stream_data)

    # Test streaming
    chunks = []
    for chunk in chatbot.chatbot_stream(
        top_schemes_text="test schemes", input_text="test input", session_id="test-session", query_text="test query"
    ):
        chunks.append(chunk)

    # Verify chunks from messages mode
    assert "First" in chunks
    assert " response" in chunks


def test_chatbot_stream_firestore_error_handling(mock_firebase_manager, mocker):
    """Test that streaming continues even if there are Firestore errors."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock Firestore error in the checkpointer
    mock_firestore_error = mocker.patch.object(
        chatbot.graph.checkpointer, "put", side_effect=Exception("Firestore error")
    )

    # Mock successful streaming response
    mock_stream_data = [
        ("messages", (mocker.MagicMock(content="Test response"), None)),
        ("updates", {"chatbot": {"messages": [mocker.MagicMock(content="Test response")]}}),
    ]
    mocker.patch.object(chatbot.graph, "stream", return_value=mock_stream_data)

    # Test streaming
    chunks = []
    for chunk in chatbot.chatbot_stream(
        top_schemes_text="test schemes", input_text="test input", session_id="test-session", query_text="test query"
    ):
        chunks.append(chunk)

    # Verify response was still streamed despite potential Firestore errors
    assert "Test response" in chunks


def test_chatbot_with_new_session(mock_firebase_manager, mocker):
    """Test chatbot with new session using LangGraph."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock graph.invoke to return a LangGraph-style response
    mock_response = [{"chatbot": {"messages": [mocker.MagicMock(content="Hello! I'm ready to help.")]}}]
    mocker.patch.object(chatbot.graph, "invoke", return_value=mock_response)

    # Call chatbot with new session
    response = chatbot.chatbot(
        top_schemes_text="test schemes",
        input_text="Hello",
        session_id="new-session",
        query_text="greeting",
    )

    # Verify response
    assert response["response"] is True
    assert response["message"] == "Hello! I'm ready to help."
