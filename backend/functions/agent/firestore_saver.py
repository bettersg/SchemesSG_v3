"""This is to preserve current session management with Firestore document storage.
Referenced https://github.com/skamalj/langgraph_checkpoint_firestore/tree/main

Supports both sync and async LangGraph checkpoint APIs.
"""

import asyncio
import base64
import json
import threading
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
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
        """Serialize objects using typed serde payloads.

        JsonPlusSerializer exposes dumps_typed/loads_typed (not dumps/loads).
        Persist as JSON so Firestore stores a plain string.
        """
        type_name, data = self.serde.dumps_typed(obj)
        payload = {
            "__type__": type_name,
            "__data__": base64.b64encode(data).decode("utf-8"),
        }
        return json.dumps(payload)

    def loads(self, serialized_obj):
        """Deserialize typed payload strings with legacy fallbacks.

        Supports:
        - current typed JSON envelope
        - already-materialized dict objects
        - legacy base64 strings (best-effort)
        """
        if isinstance(serialized_obj, dict):
            type_name = serialized_obj.get("__type__")
            data_b64 = serialized_obj.get("__data__")
            if isinstance(type_name, str) and isinstance(data_b64, str):
                data = base64.b64decode(data_b64.encode("utf-8"))
                return self.serde.loads_typed((type_name, data))
            return serialized_obj

        if not isinstance(serialized_obj, str):
            return serialized_obj

        try:
            parsed = json.loads(serialized_obj)
            if isinstance(parsed, dict):
                type_name = parsed.get("__type__")
                data_b64 = parsed.get("__data__")
                if isinstance(type_name, str) and isinstance(data_b64, str):
                    data = base64.b64decode(data_b64.encode("utf-8"))
                    return self.serde.loads_typed((type_name, data))
                return parsed
        except Exception:
            pass

        # Legacy fallback: raw base64 payload.
        try:
            raw = base64.b64decode(serialized_obj.encode("utf-8"))
            if hasattr(self.serde, "loads"):
                return self.serde.loads(raw)
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                return raw.decode("utf-8", errors="ignore")
        except Exception:
            return serialized_obj


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
            initial_history = ChatMessageHistory(messages=[])
            self._initialize_session(session_id)
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
                    tool_calls = msg.get("tool_calls") if isinstance(msg.get("tool_calls"), list) else None
                    if tool_calls:
                        messages.append(AIMessage(content=msg["content"], tool_calls=tool_calls))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "tool":
                    tool_call_id = msg.get("tool_call_id")
                    tool_name = msg.get("name")
                    messages.append(
                        ToolMessage(
                            content=msg["content"],
                            tool_call_id=str(tool_call_id) if tool_call_id else "",
                            name=str(tool_name) if tool_name else None,
                        )
                    )
            elif isinstance(msg, str):
                messages.append(AIMessage(content=msg))
        return messages

    def _initialize_session(self, session_id: str) -> None:
        """Initialize a new session in Firestore."""
        with self.__class__._lock:
            try:
                ref = self.client.collection(self.checkpoints_collection).document(session_id)
                current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                ref.set(
                    {
                        "v": 4,
                        "messages": [],
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
        """Save a checkpoint to a subcollection to avoid hitting the 1MB document limit."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "chat")
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id", "")

        channel_values = checkpoint.get("channel_values", {}) if isinstance(checkpoint, dict) else {}
        firestore_messages = []
        messages_source = None

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
                        payload = {"role": "assistant", "content": msg.content}
                        tool_calls = getattr(msg, "tool_calls", None)
                        if isinstance(tool_calls, list) and tool_calls:
                            payload["tool_calls"] = tool_calls
                        firestore_messages.append(payload)
                    elif msg.type == "tool":
                        firestore_messages.append(
                            {
                                "role": "tool",
                                "content": msg.content,
                                "name": getattr(msg, "name", None),
                                "tool_call_id": getattr(msg, "tool_call_id", None),
                            }
                        )
                else:
                    firestore_messages.append(str(msg))

        # --- OPTIMIZATION: Extract mirrors, but keep payload lightweight if needed ---
        search_history = channel_values.get("search_history", []) if isinstance(channel_values, dict) else []
        tool_history = channel_values.get("tool_history", []) if isinstance(channel_values, dict) else []
        schemes_history = channel_values.get("schemes_history", []) if isinstance(channel_values, dict) else []

        schemes_history_docs = []
        if isinstance(schemes_history, list):
            for turn in schemes_history:
                if isinstance(turn, list):
                    schemes_history_docs.append({"schemes": [s for s in turn if isinstance(s, dict)]})
                else:
                    schemes_history_docs.append({"schemes": []})

        data = {
            "v": checkpoint.get("v", 4),
            "messages": firestore_messages,
            # Serialized full state (This is the heavy hitter)
            "channel_values": self.serializer.dumps(channel_values),
            # If UI mirrors are making you exceed 1MB *per turn*, consider omitting them,
            # or trust the new subcollection architecture to give them breathing room.
            "search_history": search_history if isinstance(search_history, list) else [],
            "tool_history": tool_history if isinstance(tool_history, list) else [],
            "schemes_history": schemes_history_docs,
            "schemes_history_count": len(schemes_history) if isinstance(schemes_history, list) else 0,
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "checkpoint_id": checkpoint_id,
            "parent_checkpoint_id": parent_checkpoint_id,
            "metadata": self.serializer.dumps(metadata),
            "versions": self.serializer.dumps(new_versions),
        }

        # Store additional checkpoint fields
        for key, value in checkpoint.items():
            if key not in ["id", "ts", "channel_values", "channel_versions", "versions_seen", "v"]:
                try:
                    if isinstance(value, (str, int, float, bool, type(None))):
                        data[f"checkpoint_{key}"] = value
                    else:
                        data[f"checkpoint_{key}"] = self.serializer.dumps(value)
                except Exception as e:
                    logger.warning(f"Could not serialize checkpoint field {key}: {e}")
                    data[f"checkpoint_{key}"] = str(value)

        # --- OPTIMIZATION: Save as a unique document inside a subcollection ---
        # Path: chatHistory/{thread_id}/checkpoints/{checkpoint_id}
        ref = (
            self.client.collection(self.checkpoints_collection)
            .document(thread_id)
            .collection("checkpoints")
            .document(checkpoint_id)
        )
        ref.set(data)

        # Also update a lightweight pointer on the root document for "latest" status
        root_ref = self.client.collection(self.checkpoints_collection).document(thread_id)
        root_ref.set({"latest_checkpoint_id": checkpoint_id, "last_updated": data["last_updated"]}, merge=True)

        return {
            "configurable": {"thread_id": thread_id, "checkpoint_ns": checkpoint_ns, "checkpoint_id": checkpoint_id}
        }

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Retrieve a checkpoint tuple from the Firestore subcollection."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "chat")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        with self.__class__._lock:
            try:
                # 1. If checkpoint_id isn't provided, find the latest one from the root doc
                if not checkpoint_id:
                    root_ref = self.client.collection(self.checkpoints_collection).document(thread_id)
                    root_doc = root_ref.get()
                    if not root_doc.exists:
                        return None
                    checkpoint_id = root_doc.to_dict().get("latest_checkpoint_id")
                    if not checkpoint_id:
                        return None

                # 2. Fetch the specific checkpoint document from the subcollection
                ref = (
                    self.client.collection(self.checkpoints_collection)
                    .document(thread_id)
                    .collection("checkpoints")
                    .document(checkpoint_id)
                )
                doc = ref.get()

                if not doc.exists:
                    return None

                raw_data = doc.to_dict()

                # Reconstruct channel_versions
                versions_data = raw_data.get("versions", {})
                channel_versions = (
                    self.serializer.loads(versions_data) if isinstance(versions_data, str) else versions_data
                )

                # Reconstruct checkpoint
                channel_values_data = raw_data.get("channel_values")
                mirror_schemes_history = raw_data.get("schemes_history", [])
                mirror_search_history = raw_data.get("search_history", [])
                mirror_tool_history = raw_data.get("tool_history", [])

                reconstructed_schemes_history = []
                if isinstance(mirror_schemes_history, list):
                    for item in mirror_schemes_history:
                        if isinstance(item, dict) and isinstance(item.get("schemes"), list):
                            reconstructed_schemes_history.append(
                                [s for s in item.get("schemes", []) if isinstance(s, dict)]
                            )

                fallback_channel_values = {
                    "messages": raw_data.get("messages", []),
                    "search_history": mirror_search_history if isinstance(mirror_search_history, list) else [],
                    "tool_history": mirror_tool_history if isinstance(mirror_tool_history, list) else [],
                    "schemes_history": reconstructed_schemes_history,
                }

                if isinstance(channel_values_data, str):
                    try:
                        channel_values = self.serializer.loads(channel_values_data)
                    except Exception as e:
                        logger.warning(f"Could not deserialize channel_values: {e}")
                        channel_values = fallback_channel_values
                elif isinstance(channel_values_data, dict):
                    channel_values = channel_values_data
                else:
                    channel_values = fallback_channel_values

                checkpoint = {
                    "v": raw_data.get("v", 4),
                    "id": raw_data.get("checkpoint_id", ""),
                    "ts": datetime.now(timezone.utc).timestamp(),
                    "channel_values": channel_values,
                    "channel_versions": channel_versions,
                    "versions_seen": {},
                }

                # Restore additional fields
                for key, value in raw_data.items():
                    if key.startswith("checkpoint_"):
                        original_key = key.replace("checkpoint_", "", 1)
                        try:
                            if isinstance(value, str) and original_key not in ["id", "ts", "v"]:
                                checkpoint[original_key] = self.serializer.loads(value)
                            else:
                                checkpoint[original_key] = value
                        except Exception as e:
                            logger.warning(f"Could not deserialize checkpoint field {original_key}: {e}")
                            checkpoint[original_key] = value

                metadata_data = raw_data.get("metadata", {})
                metadata = self.serializer.loads(metadata_data) if isinstance(metadata_data, str) else metadata_data

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

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async wrapper for get_tuple used by async graph execution."""
        return await asyncio.to_thread(self.get_tuple, config)

    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Async wrapper for get used by async graph execution."""
        return await asyncio.to_thread(self.get, config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Async wrapper for put used by async graph execution."""
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config: RunnableConfig, writes: List[Tuple[str, Any]], task_id: str) -> None:
        """Async wrapper for put_writes used by async graph execution."""
        await asyncio.to_thread(self.put_writes, config, writes, task_id)
