"""Temporary logging/debugging helpers for the main agent runtime."""

from __future__ import annotations

import json
from typing import Any


def summarize_debug(value: Any, max_len: int = 220) -> str:
    def _json_default(obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            try:
                return obj.model_dump()
            except Exception:
                pass
        if hasattr(obj, "dict"):
            try:
                return obj.dict()
            except Exception:
                pass
        return repr(obj)

    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=True, default=_json_default)
        except Exception:
            text = repr(value)

    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}...<truncated>"


def log_agent_debug(response: Any) -> None:
    print("\n[agent]")
    print(f"- response preview: {summarize_debug(getattr(response, 'content', ''))}")
    print(f"- tool calls: {summarize_debug(getattr(response, 'tool_calls', []))}")


def log_postprocess_debug(meta: dict[str, Any]) -> None:
    print("\n[postprocess]")
    print(f"- removed tool-related messages: {meta.get('removed_messages_count', 0)}")
    print(f"- tool_history appended: {meta.get('tool_messages_count', 0)}")
