"""Generic runtime engine for the main assistant with tools."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import CachePolicy
from agent.firestore_saver import FirestoreChatSaver
from agent.tools.filter_rerank import filter_rerank_by_indices_tool, set_filter_rerank_context
from agent.tools.load_skill import load_skills_tool
from agent.tools.search import search_schemes_tool
from agent.tools.websearch import duckduckgo_web_search_tool
from ml_logic.cache import InMemoryCacheWithMaxsize
from .config import MainAgentRuntimeConfig
from .context_manager import MainAgentContextManager, MainAgentState
from .helpers import log_agent_debug, log_postprocess_debug, summarize_debug
from .prompt import render_main_agent_system_prompt


CONTENT_FILTER_FALLBACK_TEXT = (
    "I could not process that request due to safety filtering. "
    "Please rephrase your request in a neutral way and avoid sensitive jailbreak-style instructions."
)


def _extract_latest_user_text(messages: list[Any]) -> str:
    for message in reversed(messages):
        msg_type = getattr(message, "type", "")
        if msg_type in {"human", "user"}:
            return str(getattr(message, "content", "") or "")

        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content", "") or "")

    return ""


def _build_message_progress_fingerprint(messages: list[Any]) -> dict[str, Any]:
    """Capture in-flight graph progress not yet persisted to tool_history.

    During agent->tools->sync_current_results loops, tool_history is only updated in
    postprocess. If cache keys ignore in-flight messages, stale tool-call outputs can
    be replayed repeatedly.
    """

    total_messages = len(messages)
    trailing_tool_messages = 0
    last_tool_call_ids: list[str] = []
    last_tool_call_names: list[str] = []
    last_message_type = ""
    last_message_content_hash = ""

    if messages:
        last_message = messages[-1]
        last_message_type = str(getattr(last_message, "type", "") or "")
        last_content = str(getattr(last_message, "content", "") or "")
        last_message_content_hash = hashlib.sha1(last_content.encode("utf-8")).hexdigest()

    for msg in reversed(messages):
        if getattr(msg, "type", "") == "tool":
            trailing_tool_messages += 1
            continue
        break

    for msg in reversed(messages):
        tool_calls = getattr(msg, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                tc_id = tc.get("id")
                tc_name = tc.get("name")
                if isinstance(tc_id, str) and tc_id:
                    last_tool_call_ids.append(tc_id)
                if isinstance(tc_name, str) and tc_name:
                    last_tool_call_names.append(tc_name)
            break

    return {
        "messages_count": total_messages,
        "trailing_tool_messages": trailing_tool_messages,
        "last_tool_call_ids": sorted(last_tool_call_ids),
        "last_tool_call_names": sorted(last_tool_call_names),
        "last_message_type": last_message_type,
        "last_message_content_hash": last_message_content_hash,
    }


def _generate_main_agent_cache_key(state: MainAgentState) -> str:
    """Stable cache key for tool-enabled agent turns.

    Cache should vary by the latest user turn and the current tool-results context,
    which drives the system prompt and tool behavior.
    """

    messages = state.get("messages", [])
    message_list = messages if isinstance(messages, list) else []
    last_user_text = _extract_latest_user_text(message_list)
    current_results_json = str(state.get("current_results_json", "") or "")
    search_history = state.get("search_history", [])
    tool_history = state.get("tool_history", [])
    message_progress = _build_message_progress_fingerprint(message_list)

    tool_history_count = len(tool_history) if isinstance(tool_history, list) else 0
    last_tool_name = ""
    if isinstance(tool_history, list) and tool_history:
        last_entry = tool_history[-1]
        if isinstance(last_entry, dict):
            last_tool_name = str(last_entry.get("tool_name", "") or "")

    fingerprint = {
        "last_user_text": last_user_text,
        "current_results_json": current_results_json,
        "search_history_count": len(search_history) if isinstance(search_history, list) else 0,
        "tool_history_count": tool_history_count,
        "last_tool_name": last_tool_name,
        "message_progress": message_progress,
    }
    return hashlib.sha256(json.dumps(fingerprint, ensure_ascii=True, sort_keys=True).encode("utf-8")).hexdigest()


def _is_content_filter_error(err: Exception) -> bool:
    status_code = getattr(err, "status_code", None)
    body = getattr(err, "body", None)
    if isinstance(body, dict):
        error_obj = body.get("error", {})
        if isinstance(error_obj, dict) and error_obj.get("code") == "content_filter":
            return True

    response = getattr(err, "response", None)
    if response is not None:
        try:
            data = response.json()
            if isinstance(data, dict):
                error_obj = data.get("error", {})
                if isinstance(error_obj, dict) and error_obj.get("code") == "content_filter":
                    return True
        except Exception:
            pass

    err_text = str(err).lower()
    return status_code == 400 and ("content_filter" in err_text or "responsibleaipolicyviolation" in err_text)


def _sanitize_messages_for_llm(messages: list[Any]) -> list[Any]:
    """Drop orphan tool messages that violate OpenAI tool-call sequencing.

    Some checkpoint/message-removal edge cases can leave tool messages without a
    valid preceding assistant message containing matching tool_calls.
    """

    sanitized: list[Any] = []
    awaiting_tool_responses = False
    pending_tool_call_ids: set[str] = set()

    for message in messages:
        msg_type = getattr(message, "type", "")
        tool_calls = getattr(message, "tool_calls", None)

        if isinstance(tool_calls, list) and tool_calls:
            sanitized.append(message)
            awaiting_tool_responses = True
            pending_tool_call_ids = {
                str(tc.get("id")) for tc in tool_calls if isinstance(tc, dict) and isinstance(tc.get("id"), str)
            }
            continue

        if msg_type == "tool":
            tool_call_id = getattr(message, "tool_call_id", None)
            tool_call_id = str(tool_call_id) if isinstance(tool_call_id, str) else ""

            if not awaiting_tool_responses:
                continue

            # If ids exist, enforce id matching. If ids are missing, allow tool
            # messages until a non-tool message appears.
            if pending_tool_call_ids and tool_call_id and tool_call_id not in pending_tool_call_ids:
                continue

            sanitized.append(message)
            if tool_call_id and tool_call_id in pending_tool_call_ids:
                pending_tool_call_ids.remove(tool_call_id)
            continue

        awaiting_tool_responses = False
        pending_tool_call_ids.clear()
        sanitized.append(message)

    return sanitized


class MainAgentEngine:
    """Main chat runtime engine that encapsulates graph nodes and routing."""

    def __init__(self, *, firestore_client: Any | None = None, cache_maxsize: int = 1000):
        self._tools = [
            search_schemes_tool,
            filter_rerank_by_indices_tool,
            duckduckgo_web_search_tool,
            load_skills_tool,
        ]
        self._checkpointer = FirestoreChatSaver(client=firestore_client) if firestore_client is not None else None
        self._cache = InMemoryCacheWithMaxsize(maxsize=cache_maxsize)
        self.graph = self._build_graph()

    @staticmethod
    def initial_state() -> MainAgentState:
        return {
            "messages": [],
            "schemes_history": [],
            "search_history": [],
            "tool_history": [],
            "current_results_json": "",
        }

    def _build_llm_with_tools(self):
        cfg = MainAgentRuntimeConfig()
        llm = init_chat_model(
            cfg.provider_model_name,
            azure_deployment=cfg.azure_deployment,
            api_version=cfg.openai_api_version,
            temperature=cfg.temperature,
            model_kwargs={"max_completion_tokens": cfg.max_completion_tokens},
        )
        return llm.bind_tools(self._tools, parallel_tool_calls=True)

    async def call_chat_llm(self, state: MainAgentState) -> dict[str, Any]:
        llm_with_tools = self._build_llm_with_tools()
        context = MainAgentContextManager(state)
        current_schemes = context.get_current_schemes_for_prompt()
        set_filter_rerank_context(json.dumps({"data": current_schemes}, ensure_ascii=True))
        messages = state.get("messages", [])
        safe_messages = _sanitize_messages_for_llm(messages if isinstance(messages, list) else [])

        system = SystemMessage(
            content=render_main_agent_system_prompt(
                search_history_summary=context.summarize_search_history(),
                compact_schemes_json=summarize_debug(
                    context.compact_schemes(current_schemes, max_items=10), max_len=1000
                ),
            )
        )
        try:
            response = await llm_with_tools.ainvoke([system] + safe_messages)
        except Exception as err:
            if _is_content_filter_error(err):
                response = AIMessage(content=CONTENT_FILTER_FALLBACK_TEXT)
            else:
                raise

        log_agent_debug(response)
        return {"messages": [response]}

    def sync_current_results_from_tools(self, state: MainAgentState) -> dict[str, Any]:
        return MainAgentContextManager(state).build_sync_current_results_update()

    def postprocess_tool_messages(self, state: MainAgentState) -> dict[str, Any]:
        updates = MainAgentContextManager(state).build_postprocess_update()
        if not updates:
            return {}

        meta = updates.pop("meta", {})
        if isinstance(meta, dict):
            log_postprocess_debug(meta)
        return updates

    @staticmethod
    def _route_after_agent(state: MainAgentState) -> str:
        last = state.get("messages", [])[-1] if state.get("messages") else None
        tool_calls = getattr(last, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            return "tools"
        return "postprocess"

    def _build_graph(self):
        builder = StateGraph(MainAgentState)
        builder.add_node(
            "agent", self.call_chat_llm, cache_policy=CachePolicy(key_func=_generate_main_agent_cache_key)
        )
        builder.add_node("tools", ToolNode(self._tools))
        builder.add_node("sync_current_results", self.sync_current_results_from_tools)
        builder.add_node("postprocess", self.postprocess_tool_messages)

        builder.add_edge(START, "agent")
        builder.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "tools": "tools",
                "postprocess": "postprocess",
            },
        )
        builder.add_edge("tools", "sync_current_results")
        builder.add_edge("sync_current_results", "agent")
        builder.add_edge("postprocess", END)
        return builder.compile(checkpointer=self._checkpointer, cache=self._cache)
