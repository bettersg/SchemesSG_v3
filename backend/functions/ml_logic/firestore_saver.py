"""This is to preserve current session management with Firestore document storage.
Referenced https://github.com/skamalj/langgraph_checkpoint_firestore/tree/main

Async methods are not implemented yet
"""

import base64
import threading
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    PendingWrite,
)
from utils.logging_setup import setup_logging

from .prompt import AI_MESSAGE


logger = setup_logging()


class FirestoreSerializer:
    def __init__(self, serde):
        self.serde = serde

    def dumps_typed(self, obj):
        type_, data = self.serde.dumps_typed(obj)
        data_base64 = base64.b64encode(data).decode("utf-8")
        return type_, data_base64

    def loads_typed(self, data):
        type_name, serialized_obj = data
        serialized_obj = base64.b64decode(serialized_obj.encode("utf-8"))
        return self.serde.loads_typed((type_name, serialized_obj))

    def dumps(self, obj):
        data = self.serde.dumps(obj)
        data_base64 = base64.b64encode(data).decode("utf-8")
        return data_base64

    def loads(self, serialized_obj):
        # serialized_obj is {'step': 1, 'source': 'loop', 'parents': {}}
        # Check if serialized_obj is already a dict (not base64 encoded)
        if isinstance(serialized_obj, dict):
            return serialized_obj
        # If it's a string, decode it
        serialized_obj = base64.b64decode(serialized_obj.encode("utf-8"))
        return self.serde.loads(serialized_obj)


class FirestoreChatSaver(BaseCheckpointSaver):
    """Firestore-based checkpoint saver that maintains compatibility with existing chat history."""

    _lock = threading.Lock()

    def __init__(self, client, checkpoints_collection: str = "chatHistory", writes_collection: str = "chatWrites"):
        super().__init__()
        self.client = client
        self.serializer = FirestoreSerializer(self.serde)
        self.checkpoints_collection = checkpoints_collection
        self.writes_collection = writes_collection

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        Method to get session history of a conversation from Firestore.
        Maintains compatibility with original method signature.
        """
        config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_ns": "chat",
            }
        }

        checkpoint_tuple = self.get_tuple(config)

        if checkpoint_tuple and checkpoint_tuple.checkpoint:
            # Extract messages from checkpoint
            messages = self._extract_messages_from_checkpoint(checkpoint_tuple.checkpoint)
            return ChatMessageHistory(messages=messages)
        else:
            # Initialize new session
            initial_history = ChatMessageHistory(messages=[AIMessage(AI_MESSAGE)])
            self._initialize_session(session_id, AI_MESSAGE)
            return initial_history

    def _extract_messages_from_checkpoint(self, checkpoint) -> List[Any]:
        """Extract messages from checkpoint data."""
        messages = []
        # Check both possible locations for messages
        raw_messages = []

        if isinstance(checkpoint, dict):
            # New format: messages in channel_values
            if "channel_values" in checkpoint and "messages" in checkpoint["channel_values"]:
                raw_messages = checkpoint["channel_values"]["messages"]
            # Old format: messages directly in checkpoint
            elif "messages" in checkpoint:
                raw_messages = checkpoint["messages"]

        for msg in raw_messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            elif isinstance(msg, str):
                messages.append(AIMessage(content=msg))
        return messages

    def _initialize_session(self, session_id: str, ai_message: str) -> None:
        """Initialize a new session in Firestore."""
        with self.__class__._lock:
            try:
                ref = self.client.collection(self.checkpoints_collection).document(session_id)
                current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                ref.set(
                    {
                        "v": 4,
                        "messages": [{"role": "assistant", "content": ai_message}],
                        "last_updated": current_timestamp + " UTC",
                        "checkpoint_id": "initial",
                        "parent_checkpoint_id": "",
                        "metadata": {},
                    }
                )
            except Exception as e:
                logger.exception("Error initializing chat session in Firestore", e)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to Firestore."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id", "")

        # Convert messages to Firestore-compatible format
        firestore_messages = []
        messages_source = None

        # Check for messages in different possible locations
        if isinstance(checkpoint, dict):
            if "channel_values" in checkpoint and "messages" in checkpoint["channel_values"]:
                messages_source = checkpoint["channel_values"]["messages"]
            elif "messages" in checkpoint:
                messages_source = checkpoint["messages"]

        if messages_source:
            for msg in messages_source:
                if hasattr(msg, "type") and hasattr(msg, "content"):
                    if msg.type == "human":
                        firestore_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai":
                        firestore_messages.append({"role": "assistant", "content": msg.content})
                else:
                    firestore_messages.append(str(msg))

        # Prepare data for Firestore
        data = {
            "v": checkpoint.get("v", 4),  # Include version field
            "messages": firestore_messages,
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "checkpoint_id": checkpoint_id,
            "parent_checkpoint_id": parent_checkpoint_id,
            "metadata": self.serializer.dumps(metadata),
            "versions": self.serializer.dumps(new_versions),
        }

        # Store additional checkpoint fields that might contain cache info
        # This preserves fields like 'pending_sends', cache-related data, etc.
        for key, value in checkpoint.items():
            if key not in ["id", "ts", "channel_values", "channel_versions", "versions_seen", "v"]:
                try:
                    # Try to serialize complex objects, store simple ones directly
                    if isinstance(value, (str, int, float, bool, type(None))):
                        data[f"checkpoint_{key}"] = value
                    else:
                        data[f"checkpoint_{key}"] = self.serializer.dumps(value)
                except Exception as e:
                    logger.warning(f"Could not serialize checkpoint field {key}: {e}")
                    # Store as string representation as fallback
                    data[f"checkpoint_{key}"] = str(value)

        # Save to Firestore
        ref = self.client.collection(self.checkpoints_collection).document(thread_id)
        ref.set(data)

        return {
            "configurable": {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns, "checkpoint_id": checkpoint_id}
        }

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Retrieve a checkpoint tuple from Firestore."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "chat")

        with self.__class__._lock:
            try:
                ref = self.client.collection(self.checkpoints_collection).document(thread_id)
                doc = ref.get()

                if not doc.exists:
                    return None

                raw_data = doc.to_dict()

                # Reconstruct channel_versions
                versions_data = raw_data.get("versions", {})
                if isinstance(versions_data, str):
                    channel_versions = self.serializer.loads(versions_data)
                else:
                    channel_versions = versions_data

                # Reconstruct checkpoint with proper version and structure
                checkpoint = {
                    "v": raw_data.get("v", 4),
                    "id": raw_data.get("checkpoint_id", ""),
                    "ts": datetime.now(timezone.utc).timestamp(),
                    "channel_values": {"messages": raw_data.get("messages", [])},
                    "channel_versions": channel_versions,
                    "versions_seen": {},
                }

                # Restore additional checkpoint fields that might contain cache info
                for key, value in raw_data.items():
                    if key.startswith("checkpoint_"):
                        original_key = key.replace("checkpoint_", "", 1)
                        try:
                            # Try to deserialize if it's a string (serialized object)
                            if isinstance(value, str) and original_key not in ["id", "ts", "v"]:
                                checkpoint[original_key] = self.serializer.loads(value)
                            else:
                                checkpoint[original_key] = value
                        except Exception as e:
                            logger.warning(f"Could not deserialize checkpoint field {original_key}: {e}")
                            checkpoint[original_key] = value  # Reconstruct metadata
                metadata_data = raw_data.get("metadata", {})
                if isinstance(metadata_data, str):
                    metadata = self.serializer.loads(metadata_data)
                else:
                    metadata = metadata_data

                # Reconstruct parent config
                parent_checkpoint_id = raw_data.get("parent_checkpoint_id", "")
                parent_config = None
                if parent_checkpoint_id:
                    parent_config = {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": parent_checkpoint_id,
                        }
                    }

                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=parent_config,
                    pending_writes=None,
                )
            except Exception as e:
                logger.error(f"Error retrieving checkpoint tuple: {e}")
                return None

    def put_writes(self, config: RunnableConfig, writes: List[Tuple[str, Any]], task_id: str) -> None:
        """Fault-tolerance
        Lastly, checkpointing also provides fault-tolerance and error recovery: if one or more nodes fail at a given superstep, you can restart your graph from the last successful step. Additionally, when a graph node fails mid-execution at a given superstep, LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that superstep, so that whenever we resume graph execution from that superstep we don't re-run the successful nodes.

        Pending writes
        Additionally, when a graph node fails mid-execution at a given superstep, LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that superstep, so that whenever we resume graph execution from that superstep we don't re-run the successful nodes."""
        # Implement if you need write tracking
        pass

    def _load_pending_writes(self, thread_id: str, checkpoint_ns: str, checkpoint_id: str) -> List[PendingWrite]:
        """Load pending writes (optional implementation)."""
        return []

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Retrieve a checkpoint from Firestore."""
        tuple_result = self.get_tuple(config)
        return tuple_result.checkpoint if tuple_result else None
