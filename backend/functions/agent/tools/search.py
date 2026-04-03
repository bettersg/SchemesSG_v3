"""Tools defined for agent use."""

import asyncio
import json
import os
from typing import Any, Literal

from fb_manager.firebaseManager import FirebaseManager
from langchain_core.tools import StructuredTool
from ml_logic.searchModelManager import PaginatedSearchParams, SearchModel
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging


logger = setup_logging(level=os.getenv("AGENT_DEBUG_LOG_LEVEL", "DEBUG"))


def _truncate_text(value: str, max_len: int = 500) -> str:
    if len(value) <= max_len:
        return value
    return f"{value[:max_len]}...<truncated:{len(value) - max_len} chars>"


def _debug_serialize(value: Any, *, max_items: int = 10, max_text_len: int = 500) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _truncate_text(value, max_len=max_text_len)

    if isinstance(value, dict):
        serialized: dict[str, Any] = {}
        items = list(value.items())
        for idx, (k, v) in enumerate(items):
            if idx >= max_items:
                serialized["__truncated_keys__"] = len(items) - max_items
                break
            serialized[str(k)] = _debug_serialize(v, max_items=max_items, max_text_len=max_text_len)
        return serialized

    if isinstance(value, list):
        serialized = [_debug_serialize(v, max_items=max_items, max_text_len=max_text_len) for v in value[:max_items]]
        if len(value) > max_items:
            serialized.append({"__truncated_items__": len(value) - max_items})
        return serialized

    return _truncate_text(repr(value), max_len=max_text_len)


def _log_debug(event: str, payload: Any) -> None:
    try:
        logger.info(f"{event} | {json.dumps(_debug_serialize(payload), ensure_ascii=True)}")
    except Exception:
        logger.info(f"{event} | <payload_serialization_failed>")


class SchemeSearchToolInput(BaseModel):
    query: str = Field(..., description="Natural language query about scheme eligibility, benefits, or requirements")
    top_k: int = Field(
        default=30,
        ge=10,
        le=50,
        description="Number of search results to return (between 10 and 50)",
    )


def _search_schemes_sync(
    query: str,
    top_k: int = 30,
):
    logger.info("search_schemes tool invoked")
    top_k = max(10, min(int(top_k), 50))

    _log_debug(
        "tool.search_schemes.input",
        {
            "query": query,
            "top_k": top_k,
        },
    )

    model = SearchModel(FirebaseManager())
    params = PaginatedSearchParams(
        query=query,
        # Return a full first page sized to requested top_k for tool usage.
        limit=top_k,
        top_k=top_k,
        cursor=None,
        similarity_threshold=None,
        filters={},
        is_warmup=False,
    )
    results = model.predict_paginated(params)
    logger.info("search_schemes tool completed")
    return results


async def _search_schemes_async(
    query: str,
    top_k: int = 30,
) -> dict[str, Any]:
    logger.info("search_schemes async wrapper invoked")
    _log_debug(
        "tool.search_schemes.async_input",
        {
            "query": query,
            "top_k": top_k,
        },
    )
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_search_schemes_sync, query, top_k),
            timeout=8.0,
        )
        _log_debug("tool.search_schemes.async_output", {"query": query, "top_k": top_k, "result": result})
        return result
    except asyncio.TimeoutError:
        logger.warning("search_schemes timed out after 8s")
        _log_debug("tool.search_schemes.async_timeout", {"query": query, "top_k": top_k})
        return {"error": "search_schemes timed out after 8s"}
    except Exception as e:
        logger.exception("search_schemes failed")
        _log_debug("tool.search_schemes.async_error", {"query": query, "top_k": top_k, "error": str(e)})
        return {"error": f"search_schemes failed: {e}"}


search_schemes_tool = StructuredTool.from_function(
    func=_search_schemes_sync,
    coroutine=_search_schemes_async,
    name="search_schemes",
    description=("Search for schemes relevant to the user's query. "),
    args_schema=SchemeSearchToolInput,
)

# Example usage in an agent:
if __name__ == "__main__":
    from langgraph.prebuilt import ToolNode, tools_condition

    # Test the tool with a sample query
    test_query = "What schemes are available for small business owners affected by COVID-19?"
    result = _search_schemes_sync(test_query, top_k=20)
    print(result.keys())
    print(len(result["data"]))
    print(result["data"][0].keys())
