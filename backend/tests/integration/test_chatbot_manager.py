"""Integration tests for chatbotManager.py."""

import pytest
from datetime import datetime, timezone
from ml_logic.chatbotManager import Chatbot
from langchain_core.messages import AIMessage, HumanMessage


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


def test_chatbot_initialization(mock_firebase_manager, mocker):
    """Test Chatbot initialization with Azure and Firebase."""
    mock_azure = mocker.patch("ml_logic.chatbotManager.AzureChatOpenAI")
    mock_config = mocker.patch("ml_logic.chatbotManager.Config")

    # Configure mock config
    mock_config.return_value.deployment = "test-deployment"
    mock_config.return_value.endpoint = "test-endpoint"

    chatbot = Chatbot(mock_firebase_manager)

    assert chatbot.initialised
    assert chatbot.firebase_manager is mock_firebase_manager
    assert hasattr(chatbot, "cache")
    mock_azure.assert_called_once()


def test_get_session_history_new_session(mock_firebase_manager, mocker):
    """Test getting chat history for a new session."""
    # Set up mock chain
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False

    mock_document = mocker.MagicMock()
    mock_document.get.return_value = mock_doc

    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_document

    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    chatbot = Chatbot(mock_firebase_manager)
    history = chatbot.get_session_history("new_session")

    # Verify initial message
    assert len(history.messages) == 1
    assert isinstance(history.messages[0], AIMessage)
    assert "Welcome to Scheme Support Chat!" in history.messages[0].content

    # Verify Firestore operations
    mock_firebase_manager.firestore_client.collection.assert_called_with("chatHistory")
    mock_collection.document.assert_called_with("new_session")
    mock_document.set.assert_called_once()


def test_get_session_history_existing_session(mock_firebase_manager, mocker):
    """Test getting chat history for an existing session."""
    # Set up mock chain
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "messages": [
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Hi there"},
            {"role": "assistant", "content": "How can I help?"},
        ]
    }

    mock_document = mocker.MagicMock()
    mock_document.get.return_value = mock_doc

    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_document

    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    chatbot = Chatbot(mock_firebase_manager)
    history = chatbot.get_session_history("existing_session")

    # Verify message history
    assert len(history.messages) == 3
    assert isinstance(history.messages[0], AIMessage)
    assert isinstance(history.messages[1], HumanMessage)
    assert isinstance(history.messages[2], AIMessage)
    assert history.messages[0].content == "Hello!"
    assert history.messages[1].content == "Hi there"
    assert history.messages[2].content == "How can I help?"

    # Verify Firestore operations
    mock_firebase_manager.firestore_client.collection.assert_called_with("chatHistory")
    mock_collection.document.assert_called_with("existing_session")


def test_chatbot_cache_hit(mock_firebase_manager):
    """Test chatbot method with cache hit."""
    chatbot = Chatbot(mock_firebase_manager)

    # Set up cache
    query = "test query"
    input_text = "test input"
    cache_key = chatbot._generate_cache_key(query, input_text)
    cached_response = "Cached response"
    chatbot.cache.update("azure_openai_chatbot", cache_key, cached_response)

    # Test cache hit
    response = chatbot.chatbot("test schemes", input_text, "test_session", query)
    assert response["response"] is True
    assert response["message"] == cached_response


@pytest.mark.asyncio
async def test_chatbot_stream(mock_firebase_manager, mocker):
    """Test chatbot streaming functionality."""
    mock_azure = mocker.patch("ml_logic.chatbotManager.AzureChatOpenAI")
    chatbot = Chatbot(mock_firebase_manager)

    # Mock the streaming response
    mock_response = mocker.MagicMock()
    mock_response.content = "Test response"
    mock_azure.return_value.stream = mocker.MagicMock(return_value=[mock_response])

    # Test streaming
    async for chunk in chatbot.chatbot_stream("test schemes", "test input", "test_session", "test query"):
        assert isinstance(chunk, str)
        assert len(chunk) > 0


@pytest.mark.asyncio
async def test_chatbot_stream_with_history_update(mock_firebase_manager, mocker):
    """Test streaming with chat history updates."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock Firestore document
    mock_doc = mocker.MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"messages": [{"role": "assistant", "content": "Previous message"}]}

    # Set up Firestore mock chain
    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc
    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_ref
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    # Mock LLM streaming response
    mock_chunk1 = mocker.MagicMock()
    mock_chunk1.content = "First"
    mock_chunk2 = mocker.MagicMock()
    mock_chunk2.content = " response"
    mock_chain = mocker.MagicMock()
    mock_chain.stream.return_value = [mock_chunk1, mock_chunk2]

    # Mock prompt template and chain creation
    mocker.patch("ml_logic.chatbotManager.ChatPromptTemplate.from_messages")
    mocker.patch("ml_logic.chatbotManager.RunnableWithMessageHistory", return_value=mock_chain)

    # Test streaming
    chunks = []
    async for chunk in chatbot.chatbot_stream(
        top_schemes_text="test schemes", input_text="test input", session_id="test-session", query_text="test query"
    ):
        chunks.append(chunk)

    # Verify chunks
    assert len(chunks) == 2
    assert chunks[0] == "First"
    assert chunks[1] == " response"

    # Verify chat history update
    expected_messages = [
        {"role": "assistant", "content": "Previous message"},
        {"role": "user", "content": "test input"},
        {"role": "assistant", "content": "First response"},
    ]
    mock_ref.set.assert_called_once()
    call_args = mock_ref.set.call_args[0][0]
    assert "messages" in call_args
    assert call_args["messages"] == expected_messages
    assert "last_updated" in call_args


@pytest.mark.asyncio
async def test_chatbot_stream_cache_hit(mock_firebase_manager, mocker):
    """Test streaming with cache hit."""
    chatbot = Chatbot(mock_firebase_manager)

    # Set up cache
    query = "test query"
    input_text = "test input"
    cache_key = chatbot._generate_cache_key(query, input_text)
    cached_response = "Cached response"
    chatbot.cache.update("azure_openai_chatbot", cache_key, cached_response)

    # Test streaming with cache hit
    chunks = []
    async for chunk in chatbot.chatbot_stream(
        top_schemes_text="test schemes", input_text=input_text, session_id="test-session", query_text=query
    ):
        chunks.append(chunk)

    # Verify cached response
    assert len(chunks) == 1
    assert chunks[0] == cached_response


@pytest.mark.asyncio
async def test_chatbot_stream_firestore_error(mock_firebase_manager, mocker):
    """Test streaming when Firestore update fails."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock Firestore error
    mock_ref = mocker.MagicMock()
    mock_ref.set.side_effect = Exception("Firestore error")
    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_ref
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    # Mock LLM streaming response
    mock_chunk = mocker.MagicMock()
    mock_chunk.content = "Test response"
    mock_chain = mocker.MagicMock()
    mock_chain.stream.return_value = [mock_chunk]

    # Mock prompt template and chain creation
    mocker.patch("ml_logic.chatbotManager.ChatPromptTemplate.from_messages")
    mocker.patch("ml_logic.chatbotManager.RunnableWithMessageHistory", return_value=mock_chain)

    # Test streaming
    chunks = []
    async for chunk in chatbot.chatbot_stream(
        top_schemes_text="test schemes", input_text="test input", session_id="test-session", query_text="test query"
    ):
        chunks.append(chunk)

    # Verify response was still streamed despite Firestore error
    assert len(chunks) == 1
    assert chunks[0] == "Test response"


def test_chatbot_with_new_chat_history(mock_firebase_manager, mocker):
    """Test chatbot with new chat history creation."""
    chatbot = Chatbot(mock_firebase_manager)

    # Mock non-existent chat history
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False

    # Set up Firestore mock chain
    mock_ref = mocker.MagicMock()
    mock_ref.get.return_value = mock_doc
    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_ref
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    # Mock LLM response
    mock_message = mocker.MagicMock()
    mock_message.content = "Test response"
    mock_chain = mocker.MagicMock()
    mock_chain.invoke.return_value = mock_message

    # Mock prompt template and chain creation
    mocker.patch("ml_logic.chatbotManager.ChatPromptTemplate.from_messages")
    mocker.patch("ml_logic.chatbotManager.RunnableWithMessageHistory", return_value=mock_chain)

    # Test chatbot
    response = chatbot.chatbot(
        top_schemes_text="test schemes", input_text="test input", session_id="test-session", query_text="test query"
    )

    # Verify response
    assert response["response"] is True
    assert response["message"] == "Test response"

    # Verify new chat history creation
    mock_ref.set.assert_called_once()
    call_args = mock_ref.set.call_args[0][0]
    assert "messages" in call_args
    assert len(call_args["messages"]) == 2  # User message and assistant response
    assert call_args["messages"][0]["role"] == "user"
    assert call_args["messages"][1]["role"] == "assistant"
    assert "last_updated" in call_args
