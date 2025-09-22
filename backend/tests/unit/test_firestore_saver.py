from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langgraph.checkpoint.base import CheckpointTuple
from ml_logic.firestore_saver import FirestoreChatSaver, FirestoreSerializer
from ml_logic.prompt import AI_MESSAGE


# Mock Serializable object for serializer
class MockSerde:
    def dumps_typed(self, obj):
        return "type", b"serialized"

    def loads_typed(self, data):
        return {"restored": True}

    def dumps(self, obj):
        return b"serialized"

    def loads(self, data):
        return {"restored": True}


@pytest.fixture
def mock_client():
    """Mock Firestore client with collection/document behavior."""
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = False
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    client = MagicMock()
    client.collection.return_value = mock_collection
    return client


@pytest.fixture
def saver(mock_client):
    """Create FirestoreChatSaver with mocked client and serializer."""
    saver = FirestoreChatSaver(mock_client)
    saver.serializer = FirestoreSerializer(MockSerde())
    return saver


def test_initialize_session_creates_document(saver, mock_client):
    """_initialize_session should call set on Firestore document."""
    session_id = "test_session"
    with patch("ml_logic.firestore_saver.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2025, 1, 1, tzinfo=timezone.utc)
        mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
        saver._initialize_session(session_id, "Hello AI")

    # Verify Firestore set was called
    doc_ref = mock_client.collection.return_value.document.return_value
    assert doc_ref.set.called
    args, kwargs = doc_ref.set.call_args
    assert "messages" in args[0]
    assert args[0]["messages"][0]["content"] == "Hello AI"


def test_firestore_saver_get_session_history_new_session(mock_firebase_manager, mocker):
    """Test FirestoreChatSaver returns a new session when no checkpoint exists."""

    # Create the Firestore saver with a mock client
    saver = FirestoreChatSaver(client=mock_firebase_manager)

    # Patch Firestore document to not exist
    mock_doc = mocker.MagicMock()
    mock_doc.exists = False

    mock_document = mocker.MagicMock()
    mock_document.get.return_value = mock_doc

    mock_collection = mocker.MagicMock()
    mock_collection.document.return_value = mock_document

    mock_firebase_manager.collection.return_value = mock_collection
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    # Call get_session_history
    history = saver.get_session_history("new_session")

    # Verify it returns a ChatMessageHistory with the initial AI message
    assert isinstance(history, ChatMessageHistory)
    assert len(history.messages) == 1
    assert isinstance(history.messages[0], AIMessage)
    assert AI_MESSAGE in history.messages[0].content

    # Verify Firestore set was called to initialize session
    mock_document.set.assert_called_once()
    mock_collection.document.assert_called_with("new_session")


def test_firestore_saver_get_session_history_existing_session(mock_firebase_manager, mocker):
    """Test FirestoreChatSaver returns the correct history for an existing session."""

    # Create Firestore saver
    saver = FirestoreChatSaver(client=mock_firebase_manager)

    # Mock checkpoint with messages
    checkpoint = {
        "messages": [
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Hi there"},
            {"role": "assistant", "content": "How can I help?"},
        ]
    }

    # Patch get_tuple to return a checkpoint tuple
    mocker.patch.object(
        saver,
        "get_tuple",
        return_value=CheckpointTuple(
            config={"configurable": {"thread_id": "existing_session"}},
            checkpoint=checkpoint,
            metadata={},
            parent_config=None,
            pending_writes=None,
        ),
    )

    # Call get_session_history
    history = saver.get_session_history("existing_session")

    # Verify message history
    assert len(history.messages) == 3
    assert isinstance(history.messages[0], AIMessage)
    assert isinstance(history.messages[1], HumanMessage)
    assert isinstance(history.messages[2], AIMessage)
    assert history.messages[0].content == "Hello!"
    assert history.messages[1].content == "Hi there"
    assert history.messages[2].content == "How can I help?"


def test_get_session_history_with_existing_checkpoint(saver):
    """get_session_history returns messages from checkpoint if exists."""
    # Mock get_tuple to return a checkpoint
    checkpoint_data = {"channel_values": {"messages": [{"role": "user", "content": "hi"}]}}
    saver.get_tuple = MagicMock(return_value=MagicMock(checkpoint=checkpoint_data))
    history = saver.get_session_history("session1")
    assert isinstance(history.messages[0], HumanMessage)
    assert history.messages[0].content == "hi"


def test_extract_messages_from_checkpoint_handles_formats(saver):
    """_extract_messages_from_checkpoint correctly converts checkpoint messages."""
    checkpoint = {
        "channel_values": {
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
                "plain string message",
            ]
        }
    }
    messages = saver._extract_messages_from_checkpoint(checkpoint)
    assert len(messages) == 3
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage)
    assert isinstance(messages[2], AIMessage)


def test_put_stores_data_in_firestore(saver):
    """put should call set on Firestore with serialized data."""
    config = {"configurable": {"thread_id": "thread1", "checkpoint_ns": "chat"}}
    checkpoint = {"id": "ckpt1", "messages": [MagicMock(type="human", content="hi")]}
    metadata = {"meta": "data"}
    new_versions = {"v1": 1}

    result = saver.put(config, checkpoint, metadata, new_versions)

    doc_ref = saver.client.collection.return_value.document.return_value
    doc_ref.set.assert_called_once()
    # Returned config should contain checkpoint_id
    assert result["configurable"]["checkpoint_id"] == "ckpt1"


def test_get_tuple_returns_none_when_doc_missing(saver):
    """get_tuple returns None if Firestore document does not exist."""
    config = {"configurable": {"thread_id": "missing"}}
    result = saver.get_tuple(config)
    assert result is None


def test_get_tuple_reconstructs_checkpoint(saver):
    """get_tuple reconstructs checkpoint and metadata from Firestore doc."""
    # Mock serializer to avoid base64 decoding issues
    saver.serializer.loads = MagicMock(return_value={"restored": True})

    # Mock document to exist
    mock_doc = saver.client.collection.return_value.document.return_value
    mock_doc.get.return_value.exists = True
    mock_doc.get.return_value.to_dict.return_value = {
        "checkpoint_id": "ckpt1",
        "v": 4,
        "messages": [],
        "metadata": "any_data",
        "versions": "any_data",
        "parent_checkpoint_id": "",
    }

    config = {"configurable": {"thread_id": "thread1", "checkpoint_ns": "chat"}}
    result = saver.get_tuple(config)

    assert result is not None
    assert result.checkpoint["id"] == "ckpt1"
