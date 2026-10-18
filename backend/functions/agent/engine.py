from time import perf_counter
from typing import Any, Iterator

from integrations import FirebaseManager
from langchain_core.messages import HumanMessage
from loguru import logger
from utils.latency import log_elapsed

from .event_type import AgentStreamEventType
from .router import RouterAgentGraph
from .tracing import load_langfuse_client_and_handler


_FIRST_TURN = True


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


def process_streaming_chunk(chunk: dict) -> dict:
    if isinstance(chunk, dict) and chunk.get("type") == "messages":
        data = chunk.get("data")

        if not isinstance(data, tuple) or not data:
            return {}
        metadata = data[1]
        if metadata.get("langgraph_node") == "tools":
            return {}
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

        if content:
            return {"type": AgentStreamEventType.TEXT, "data": {"text": content}}

    return {}


def stream_chat_events(input_text: str, session_id: str) -> Iterator[dict[str, Any]]:
    """Sync generator that streams events from the graph.

    Yields dicts shaped like: {"type": "text", "data": {...}} or {"type": "custom", "data": ...}
    """
    global _FIRST_TURN

    turn_started_at = perf_counter()
    first_turn = _FIRST_TURN
    _FIRST_TURN = False
    started_at = perf_counter()
    firebase_manager = FirebaseManager()
    main_agent_graph = RouterAgentGraph(firestore_client=firebase_manager.firestore_client)
    graph = main_agent_graph.graph
    log_elapsed(logger, session_id, "request_setup", started_at, first_turn_in_process=first_turn)

    _, langfuse_handler = load_langfuse_client_and_handler()

    started_at = perf_counter()
    demo_state = restore_messages_state(graph, session_id)
    log_elapsed(logger, session_id, "checkpoint_restore", started_at)
    demo_state["messages"].append(HumanMessage(content=input_text))

    completed = False
    try:
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
                result = process_streaming_chunk(chunk)
                if result:
                    yield result
                continue

            # Yield custom chunks raw for handler parsing
            if isinstance(chunk, dict) and chunk.get("type") == "custom":
                yield chunk.get("data", {})
                continue
        completed = True
    finally:
        log_elapsed(logger, session_id, "turn_complete", turn_started_at, completed=completed)

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
