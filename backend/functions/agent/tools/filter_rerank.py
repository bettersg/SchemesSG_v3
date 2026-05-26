"""Tool to reorder/filter an existing schemes list using LLM-provided indices."""

import asyncio
import json
from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging


logger = setup_logging()
# To be used as a fallback message if LLM doesn't provide an action_message in the tool call input.
DEFAULT_LLM_ACTION_MESSAGE = "Based on your current context and preferences."
ACTION_MESSAGE_ON_START = "Filtering and re-ranking existing schemes.\n {action_message}"
ACTION_MESSAGE_ON_END = "Filtered and re-ranked schemes list to {num_items} items."

_CURRENT_RESULTS_JSON = ""


def set_filter_rerank_context(results_json: str) -> None:
    """Inject current schemes payload for rerank/filter calls in this process."""
    global _CURRENT_RESULTS_JSON
    _CURRENT_RESULTS_JSON = results_json if isinstance(results_json, str) else ""


class FilterRerankByIndicesInput(BaseModel):
    indices: list[int] = Field(
        ...,
        description=("Zero-based indices in preferred order. The tool returns only these indices, preserving order."),
    )
    action_message: str = Field(
        default="",
        description="Optional note describing why these indices were chosen.",
    )


def _extract_results_list(results_json: str) -> tuple[dict | list | None, list[dict]]:
    try:
        parsed = json.loads(results_json)
    except Exception:
        return None, []

    if isinstance(parsed, dict):
        if isinstance(parsed.get("data"), list):
            return parsed, parsed["data"]
        if isinstance(parsed.get("results"), list):
            return parsed, parsed["results"]
        return parsed, []

    if isinstance(parsed, list):
        return parsed, parsed

    return parsed, []


def _filter_rerank_by_indices_sync(
    indices: list[int],
    action_message: str = "",
) -> dict[str, Any]:
    try:
        write = get_stream_writer()
        write(
            {
                "type": "action_message",
                "message": ACTION_MESSAGE_ON_START.format(action_message=action_message or DEFAULT_LLM_ACTION_MESSAGE),
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit filter_rerank_by_indices action message to stream: {e}")

    results_json = _CURRENT_RESULTS_JSON
    if not results_json:
        return {
            "error": "No current schemes context available for rerank/filter.",
            "data": [],
            "total_count": 0,
            "selected_count": 0,
            "used_indices": [],
            "invalid_indices": indices,
            "action_message": action_message,
        }

    parsed, source_list = _extract_results_list(results_json)
    total_count = len(source_list)

    if total_count == 0:
        return {
            "data": [],
            "total_count": 0,
            "selected_count": 0,
            "used_indices": [],
            "invalid_indices": indices,
            "action_message": action_message,
        }

    used_indices: list[int] = []
    invalid_indices: list[int] = []
    seen: set[int] = set()

    for idx in indices:
        if not isinstance(idx, int):
            continue
        if idx < 0 or idx >= total_count:
            invalid_indices.append(idx)
            continue
        if idx in seen:
            continue
        seen.add(idx)
        used_indices.append(idx)

    selected = [source_list[idx] for idx in used_indices]

    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        out_payload: dict[str, Any] = dict(parsed)
        out_payload["data"] = selected
    elif isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
        out_payload = dict(parsed)
        out_payload["results"] = selected
    else:
        out_payload = {"data": selected}

    out_payload["total_count"] = total_count
    out_payload["selected_count"] = len(selected)
    out_payload["used_indices"] = used_indices
    out_payload["invalid_indices"] = invalid_indices
    out_payload["action_message"] = action_message

    try:
        write = get_stream_writer()
        write(
            {
                "type": "action_message",
                "message": ACTION_MESSAGE_ON_END.format(num_items=len(selected)),
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit filter_rerank_by_indices completion message to stream: {e}")
    return out_payload


async def _filter_rerank_by_indices_async(
    indices: list[int],
    action_message: str = "",
) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_filter_rerank_by_indices_sync, indices, action_message),
            timeout=6.0,
        )
    except asyncio.TimeoutError:
        return {"error": "filter_rerank_by_indices timed out after 6s"}
    except Exception as exc:
        return {"error": f"filter_rerank_by_indices failed: {exc}"}


filter_rerank_by_indices_tool = StructuredTool.from_function(
    func=_filter_rerank_by_indices_sync,
    coroutine=_filter_rerank_by_indices_async,
    name="filter_rerank_by_indices",
    description=(
        "Filter and reorder an existing schemes list using zero-based indices. "
        "Use after you already have current schemes and want reranking or filtering."
    ),
    args_schema=FilterRerankByIndicesInput,
)
