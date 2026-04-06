"""Context abstractions for the main tool-enabled assistant runtime."""

from __future__ import annotations

import ast
import json
from typing import Annotated, Any, TypedDict

from langchain_core.messages import RemoveMessage
from langgraph.graph.message import add_messages


class MainAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    schemes_history: list[list[dict]]
    search_history: list[dict]
    tool_history: list[dict[str, Any]]
    current_results_json: str


class MainAgentContextManager:
    """Main-agent specific context helper.

    Runtime-local state/context helper for the main agent graph.
    """

    SCHEME_SEARCH_RESULT_IMPORTANT_FIELDS = [
        "scheme",
        "llm_description",
        "what_it_gives",
        "service_area",
        "planning_area",
        "who_is_it_for",
        "agency",
        "link",
    ]

    def __init__(self, state: MainAgentState):
        self._state = state

    def summarize_search_history(self, max_items: int = 5) -> str:
        history = self._state.get("search_history", [])
        if not history:
            return "No search history."

        summary_lines: list[str] = []
        for entry in history[-max_items:]:
            query = entry.get("query", "<no query>")
            result_count = entry.get("result_count", 0)
            summary_lines.append(f"Query: '{query}' | Results: {result_count}")
        return "\n".join(summary_lines)

    def get_latest_schemes(self) -> list[dict]:
        schemes_history = self._state.get("schemes_history", [])
        if not schemes_history:
            return []
        return schemes_history[-1]

    def compact_scheme(self, scheme: dict[str, Any]) -> dict[str, Any]:
        compact: dict[str, Any] = {}
        for field in self.SCHEME_SEARCH_RESULT_IMPORTANT_FIELDS:
            value = scheme.get(field)
            if value is None or value == "" or value == [] or value == {}:
                continue
            compact[field] = value
        return compact

    def compact_schemes(self, schemes: list[dict], max_items: int | None = None) -> list[dict]:
        selected = schemes if max_items is None else schemes[:max_items]
        return [self.compact_scheme(scheme) for scheme in selected if isinstance(scheme, dict)]

    def compact_latest_schemes(self, max_items: int | None = None) -> list[dict]:
        return self.compact_schemes(self.get_latest_schemes(), max_items=max_items)

    def get_current_schemes_for_prompt(self) -> list[dict]:
        schemes_from_history = self.get_latest_schemes()
        if schemes_from_history:
            return schemes_from_history

        current_results_json = self._state.get("current_results_json", "")
        if isinstance(current_results_json, str) and current_results_json.strip():
            try:
                parsed = json.loads(current_results_json)
                schemes = self.extract_results(parsed)
                if schemes:
                    return schemes
            except Exception:
                pass
        return []

    @staticmethod
    def parse_tool_payload(content: Any) -> dict[str, Any]:
        if isinstance(content, dict):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            content = "\n".join(parts)

        if not isinstance(content, str):
            return {}

        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            pass

        try:
            parsed = ast.literal_eval(content)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def extract_results(payload: Any) -> list[dict]:
        if isinstance(payload, dict):
            if isinstance(payload.get("data"), list):
                return payload["data"]
            if isinstance(payload.get("results"), list):
                return payload["results"]
        if isinstance(payload, list):
            return payload
        return []

    @staticmethod
    def extract_query_from_tool_call(tool_call: dict[str, Any]) -> str:
        args = tool_call.get("args", {}) if isinstance(tool_call, dict) else {}
        if isinstance(args, dict):
            query = args.get("query", "")
            if isinstance(query, str) and query.strip():
                return query.strip()
        return "<no query from tool_call>"

    def build_sync_current_results_update(self) -> dict[str, Any]:
        messages = self._state.get("messages", [])

        trailing_tool_messages: list[Any] = []
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "tool":
                trailing_tool_messages.append(msg)
                continue
            if trailing_tool_messages:
                break

        trailing_tool_messages = list(reversed(trailing_tool_messages))
        if not trailing_tool_messages:
            return {}

        latest_payload: dict[str, Any] | None = None
        for msg in trailing_tool_messages:
            tool_name = getattr(msg, "name", "") or ""
            if tool_name not in {"search_schemes", "filter_rerank_by_indices"}:
                continue
            payload = self.parse_tool_payload(getattr(msg, "content", ""))
            if payload:
                latest_payload = payload

        if latest_payload is None:
            return {}

        return {"current_results_json": json.dumps(latest_payload, ensure_ascii=True)}

    def build_postprocess_update(self) -> dict[str, Any]:
        messages = self._state.get("messages", [])
        schemes_history = self._state.get("schemes_history", [])
        search_history = self._state.get("search_history", [])
        tool_history = self._state.get("tool_history", [])

        tool_messages = [msg for msg in messages if getattr(msg, "type", None) == "tool"]
        if not tool_messages:
            return {}

        tool_call_map: dict[str, dict[str, Any]] = {}
        for msg in messages:
            tool_calls = getattr(msg, "tool_calls", None)
            if not (isinstance(tool_calls, list) and tool_calls):
                continue
            for tc in tool_calls:
                if isinstance(tc, dict) and isinstance(tc.get("id"), str):
                    tool_call_map[tc["id"]] = tc

        remove_ops: list[RemoveMessage] = []
        for msg in tool_messages:
            msg_id = getattr(msg, "id", None)
            if msg_id:
                remove_ops.append(RemoveMessage(id=msg_id))

            tool_name = getattr(msg, "name", "") or ""
            payload = self.parse_tool_payload(getattr(msg, "content", ""))
            schemes = self.extract_results(payload)
            call_id = getattr(msg, "tool_call_id", None)
            tool_call = tool_call_map.get(call_id, {}) if isinstance(call_id, str) else {}

            if tool_name in {"search_schemes", "filter_rerank_by_indices"}:
                query = self.extract_query_from_tool_call(tool_call)
                schemes_history = schemes_history + [schemes]
                if tool_name == "search_schemes":
                    search_history = search_history + [{"query": query, "result_count": len(schemes)}]

            tool_history = tool_history + [
                {
                    "tool_name": tool_name,
                    "tool_call": tool_call,
                    "response": payload,
                    "result_count": len(schemes),
                }
            ]

        for msg in messages:
            tool_calls = getattr(msg, "tool_calls", None)
            if not (isinstance(tool_calls, list) and tool_calls):
                continue
            msg_id = getattr(msg, "id", None)
            if msg_id:
                remove_ops.append(RemoveMessage(id=msg_id))

        return {
            "messages": remove_ops,
            "schemes_history": schemes_history,
            "search_history": search_history,
            "tool_history": tool_history,
            "meta": {
                "removed_messages_count": len(remove_ops),
                "tool_messages_count": len(tool_messages),
            },
<<<<<<< HEAD
        }
=======
        }
>>>>>>> origin/feat/264-new-design
