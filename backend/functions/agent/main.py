"""Endpoint-ready streaming interface for the main agent runtime.

This module exposes async and sync streaming helpers that can be used by server
handlers to stream structured events to the frontend.
"""

from __future__ import annotations

import asyncio
import hashlib
import queue
import threading
from dataclasses import dataclass
from typing import Any, AsyncIterator, Iterator

from dotenv import find_dotenv, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain_core.messages import HumanMessage

from agent.event_type import AgentStreamEventType
from agent.runtimes.followup.engine import FollowupEngine
from agent.runtimes.main_agent.engine import MainAgentEngine


load_dotenv(find_dotenv())


@dataclass
class _RuntimeBundle:
    firebase_manager: FirebaseManager
    engine: MainAgentEngine
    followup_engine: FollowupEngine


_runtime_singleton: _RuntimeBundle | None = None
_runtime_lock = threading.Lock()
_bridge_loop: asyncio.AbstractEventLoop | None = None
_bridge_thread: threading.Thread | None = None
_bridge_lock = threading.Lock()

_TOOL_STATUS_LABELS: dict[str, str] = {
    "search_schemes": "Searching for relevant schemes...",
    "filter_rerank_by_indices": "Refining and prioritizing scheme matches...",
    "duckduckgo_web_search": "Checking latest public information...",
    "load_skills": "Preparing concise response style...",
}


def _get_runtime_bundle() -> _RuntimeBundle:
    """Singleton-style runtime factory for endpoint calls."""

    global _runtime_singleton
    if _runtime_singleton is not None:
        return _runtime_singleton

    with _runtime_lock:
        if _runtime_singleton is not None:
            return _runtime_singleton

        firebase_manager = FirebaseManager()
        engine = MainAgentEngine(firestore_client=firebase_manager.firestore_client)
        followup_engine = FollowupEngine()
        _runtime_singleton = _RuntimeBundle(
            firebase_manager=firebase_manager,
            engine=engine,
            followup_engine=followup_engine,
        )
        return _runtime_singleton


def _ensure_bridge_loop() -> asyncio.AbstractEventLoop:
    """Create (once) and return a long-lived background event loop."""

    global _bridge_loop, _bridge_thread
    if _bridge_loop is not None and _bridge_thread is not None and _bridge_thread.is_alive():
        return _bridge_loop

    with _bridge_lock:
        if _bridge_loop is not None and _bridge_thread is not None and _bridge_thread.is_alive():
            return _bridge_loop

        loop = asyncio.new_event_loop()

        def _run_loop() -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        thread = threading.Thread(target=_run_loop, daemon=True, name="agent-stream-bridge-loop")
        thread.start()

        _bridge_loop = loop
        _bridge_thread = thread
        return loop


def _extract_latest_assistant_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        if getattr(message, "type", "") == "ai":
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
            return str(content)
    return ""


def _extract_latest_schemes(values: dict[str, Any]) -> list[dict[str, Any]]:
    schemes_history = values.get("schemes_history", [])
    if isinstance(schemes_history, list) and schemes_history:
        last = schemes_history[-1]
        if isinstance(last, list):
            return [item for item in last if isinstance(item, dict)]
    return []


def _extract_schemes_history(values: dict[str, Any]) -> list[list[dict[str, Any]]]:
    history = values.get("schemes_history", [])
    if not isinstance(history, list):
        return []

    normalized: list[list[dict[str, Any]]] = []
    for item in history:
        if isinstance(item, list):
            normalized.append([scheme for scheme in item if isinstance(scheme, dict)])
    return normalized


def _build_schemes_signature(schemes: list[dict[str, Any]]) -> str:
    if not schemes:
        return ""

    ids: list[str] = []
    for scheme in schemes:
        if not isinstance(scheme, dict):
            continue
        scheme_id = scheme.get("scheme_id") or scheme.get("schemeId") or ""
        if scheme_id:
            ids.append(str(scheme_id))

    if ids:
        return hashlib.sha1("|".join(ids).encode("utf-8")).hexdigest()

    return hashlib.sha1(str(schemes).encode("utf-8")).hexdigest()


def _event(event_type: AgentStreamEventType, data: dict[str, Any]) -> dict[str, Any]:
    return {"type": event_type, "data": data}


def _extract_tool_call_names(message_chunk: Any) -> list[str]:
    names: list[str] = []

    tool_calls = getattr(message_chunk, "tool_calls", None)
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if isinstance(call, dict):
                name = call.get("name")
                if isinstance(name, str) and name:
                    names.append(name)

    tool_call_chunks = getattr(message_chunk, "tool_call_chunks", None)
    if isinstance(tool_call_chunks, list):
        for chunk in tool_call_chunks:
            if isinstance(chunk, dict):
                name = chunk.get("name")
                if isinstance(name, str) and name:
                    names.append(name)

    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)
    return deduped


async def stream_chat_events(input_text: str, session_id: str) -> AsyncIterator[dict[str, Any]]:
    """Stream structured chat events for frontend consumption.

    Event types emitted:
    - status
    - chunk
    - schemes_update
    - schemes
    - assistant
    - followups
    - done
    """

    runtime = _get_runtime_bundle()
    graph = runtime.engine.graph
    config = {"configurable": {"thread_id": session_id}}

    yield _event(AgentStreamEventType.STATUS, {"phase": "started", "label": "Starting analysis..."})

    # Baseline is persisted thread state before this turn; avoid re-emitting
    # schemes_update unless this turn actually changes scheme results.
    baseline_snapshot = await graph.aget_state(config=config)
    baseline_values = getattr(baseline_snapshot, "values", {}) if baseline_snapshot is not None else {}
    baseline_values = baseline_values if isinstance(baseline_values, dict) else {}
    baseline_schemes = _extract_latest_schemes(baseline_values)
    last_schemes_signature = _build_schemes_signature(baseline_schemes)
    emitted_tool_statuses: set[str] = set()

    async for mode, data in graph.astream(
        {"messages": [HumanMessage(content=input_text)]},
        config=config,
        stream_mode=["messages", "values"],
    ):
        if mode == "messages":
            message_chunk, metadata = data
            node_name = metadata.get("langgraph_node", "") if isinstance(metadata, dict) else ""

            if node_name == "agent":
                tool_names = _extract_tool_call_names(message_chunk)
                for tool_name in tool_names:
                    if tool_name in emitted_tool_statuses:
                        continue
                    emitted_tool_statuses.add(tool_name)
                    yield _event(
                        AgentStreamEventType.STATUS,
                        {
                            "phase": "tool_selected",
                            "tool_name": tool_name,
                            "label": _TOOL_STATUS_LABELS.get(tool_name, "Working on your request..."),
                        },
                    )

            token = getattr(message_chunk, "content", "")
            if isinstance(token, str) and token and node_name == "agent":
                yield _event(AgentStreamEventType.CHUNK, {"chunk": token})
            continue

        if mode == "values" and isinstance(data, dict):
            schemes = _extract_latest_schemes(data)
            current_signature = _build_schemes_signature(schemes)
            if current_signature != last_schemes_signature:
                last_schemes_signature = current_signature
                yield _event(
                    AgentStreamEventType.SCHEMES_UPDATE,
                    {
                        "schemes": schemes,
                        "total_count": len(schemes),
                        "search_history": data.get("search_history", []),
                    },
                )

    snapshot = await graph.aget_state(config=config)
    values = getattr(snapshot, "values", {}) if snapshot is not None else {}
    messages = values.get("messages", []) if isinstance(values, dict) else []
    messages = messages if isinstance(messages, list) else []

    assistant_text = _extract_latest_assistant_text(messages)
    followups = await runtime.followup_engine.generate_kv_async(messages)
    final_schemes = _extract_latest_schemes(values if isinstance(values, dict) else {})
    schemes_history = _extract_schemes_history(values if isinstance(values, dict) else {})

    yield _event(AgentStreamEventType.ASSISTANT, {"text": assistant_text})
    yield _event(
        AgentStreamEventType.SCHEMES,
        {
            "schemes_history": schemes_history,
            "total_count": len(final_schemes),
        },
    )
    yield _event(AgentStreamEventType.FOLLOWUPS, {"items": followups})
    yield _event(AgentStreamEventType.DONE, {})


def stream_chat_events_sync(input_text: str, session_id: str) -> Iterator[dict[str, Any]]:
    """Sync wrapper for frameworks that require a synchronous generator."""

    event_queue: queue.Queue[Any] = queue.Queue()
    sentinel = object()

    async def _produce() -> None:
        try:
            async for event in stream_chat_events(input_text=input_text, session_id=session_id):
                event_queue.put(event)
        except Exception as exc:
            event_queue.put(exc)
        finally:
            event_queue.put(sentinel)

    bridge_loop = _ensure_bridge_loop()
    asyncio.run_coroutine_threadsafe(_produce(), bridge_loop)

    while True:
        item = event_queue.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            raise item
        yield item


__all__ = ["stream_chat_events", "stream_chat_events_sync"]
