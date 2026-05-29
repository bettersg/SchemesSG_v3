from typing import Any, Iterator

from integrations import FirebaseManager
from langchain_core.messages import HumanMessage

from .event_type import AgentStreamEventType
from .router import RouterAgentGraph
from .tracing import load_langfuse_client_and_handler

_TARGET_TEXT_CHUNK_LEN = 300


def restore_messages_state(graph: Any, thread_id: str) -> dict[str, Any]:
    """Restore persisted messages for the thread."""

    snapshot = graph.get_state(config={"configurable": {"thread_id": thread_id}})
    values = getattr(snapshot, "values", {}) if snapshot is not None else {}
    values = values if isinstance(values, dict) else {}

    messages = values.get("messages", [])
    if not isinstance(messages, list):
        messages = []

    return {
        "messages": messages,
    }


def split_collated_chunk(collated_chunk: str) -> tuple[str, str]:
    """Split collated_chunk by the last sentence-ending punctuation within sensible bounds.

    Returns (sent_chunk, remainder).
    """
    if len(collated_chunk) < _TARGET_TEXT_CHUNK_LEN:
        return "", collated_chunk

    # look for last sentence-ending punctuation within a window
    punct_idx = -1
    for punct in (".", "?", "!", "-"):
        idx = collated_chunk.rfind(punct, 0, _TARGET_TEXT_CHUNK_LEN)
        punct_idx = max(punct_idx, idx)

    if punct_idx != -1:
        cut = punct_idx + 1
    else:
        # fallback: split at target length
        cut = min(_TARGET_TEXT_CHUNK_LEN, len(collated_chunk))

    sent = collated_chunk[:cut].strip()
    remainder = collated_chunk[cut:].lstrip()
    if not sent:
        return "", collated_chunk
    return sent, remainder


def process_streaming_chunk(chunk: dict, collated_chunk: str) -> tuple[dict, str]:
    # If this is a 'messages' chunk, try to collate small message pieces
    if isinstance(chunk, dict) and chunk.get("type") == "messages":
        data = chunk.get("data")

        if not isinstance(data, tuple) or not data:
            return {}, collated_chunk
        metadata = data[1]
        if metadata.get("langgraph_node") == "tools":
            return {}, collated_chunk
        message = data[0]
        content = getattr(message, "content", "")
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            content = "\n".join(parts)

        # Only append small-ish incoming message pieces (per spec: >0 and <200 chars)
        if content.strip() and 0 < len(content) < 200:
            collated_chunk += content

            # If collated chunk reached target length, split at last sentence boundary
            if len(collated_chunk) >= _TARGET_TEXT_CHUNK_LEN:
                sent, remainder = split_collated_chunk(collated_chunk)
                if sent:
                    return {"type": AgentStreamEventType.TEXT, "data": {"text": sent}}, remainder

        return {}, collated_chunk

    # Non-message chunk — treat as end of message sequence: release any remainder
    else:
        if len(collated_chunk.strip()) > 0:
            remainder = collated_chunk
            collated_chunk = ""
            return {"type": AgentStreamEventType.TEXT, "data": {"text": remainder}}, ""
    return {}, collated_chunk


def stream_chat_events(input_text: str, session_id: str) -> Iterator[dict[str, Any]]:
    """Sync generator that streams events from the graph.

    Yields dicts shaped like: {"type": "text", "data": {...}} or {"type": "custom", "data": ...}
    """
    firebase_manager = FirebaseManager()
    main_agent_graph = RouterAgentGraph(firestore_client=firebase_manager.firestore_client)
    graph = main_agent_graph.graph

    _, langfuse_handler = load_langfuse_client_and_handler()

    demo_state = restore_messages_state(graph, session_id)
    demo_state["messages"].append(HumanMessage(content=input_text))

    collated_chunk = ""
    for chunk in graph.stream(
        demo_state,
        config={
            "callbacks": [langfuse_handler] if langfuse_handler else [],
            "configurable": {"thread_id": session_id},
        },
        stream_mode=["messages", "custom"],
        version="v2",
    ):
        # Process message chunks into text events
        if isinstance(chunk, dict) and chunk.get("type") == "messages":
            result, collated_chunk = process_streaming_chunk(chunk, collated_chunk)
            if result:
                yield result
            continue

        # Yield custom chunks raw for handler parsing
        if isinstance(chunk, dict) and chunk.get("type") == "custom":
            # Emit any remaining collated text before yielding the custom chunk, to preserve event order
            if collated_chunk.strip():
                yield {"type": "text", "data": {"text": collated_chunk}}
            yield chunk.get("data", {})
            continue

    # final state fetch (optional) - yield a DONE marker
    yield {"type": AgentStreamEventType.DONE, "data": {}}


test = (
    "Do you know any schemes for hawkers in Singapore?"
    "If so, can you find me some that are still open for application?"
    "If not, can you search the web and find some for me?"
)

if __name__ == "__main__":
    # simple CLI runner for debugging: prints events from the async generator
    # search and filter out the mental health supposrt schemes that is for female"
    def _run_debug(
        input_text: str = "search AND filter mental health support for older adults",
        session_id: str = "000newdebugsession01",
    ):
        for ev in stream_chat_events(input_text, session_id):
            print(ev)

    _run_debug()
