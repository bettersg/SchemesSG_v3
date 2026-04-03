"""DuckDuckGo web search tool for agent use."""

import asyncio
import json
import os
from typing import Any

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging


logger = setup_logging(level=os.getenv("AGENT_DEBUG_LOG_LEVEL", "DEBUG"))


class DuckDuckGoWebSearchInput(BaseModel):
    query: str = Field(..., description="Natural language web query to search on DuckDuckGo")
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of result items to return (1-10)",
    )


def _normalize_ddg_item(item: Any) -> dict[str, str] | None:
    if not isinstance(item, dict):
        return None

    title = str(item.get("title") or item.get("snippet") or item.get("body") or "").strip()
    snippet = str(item.get("snippet") or item.get("body") or item.get("title") or "").strip()
    url = str(item.get("link") or item.get("url") or "").strip()

    if not title and not snippet:
        return None

    return {
        "title": title,
        "snippet": snippet,
        "url": url,
    }


def _duckduckgo_web_search_sync(query: str, max_results: int = 5) -> dict[str, Any]:
    max_results = max(1, min(int(max_results), 10))
    logger.info(f"duckduckgo_web_search tool invoked | query={query}")

    try:
        ddg_tool = DuckDuckGoSearchResults(max_results=max_results, output_format="list")
        raw = ddg_tool.invoke(query)

        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []

        items = raw if isinstance(raw, list) else []
        results: list[dict[str, str]] = []

        for item in items:
            normalized = _normalize_ddg_item(item)
            if normalized is None:
                continue
            results.append(normalized)
            if len(results) >= max_results:
                break

        return {
            "query": query,
            "source": "duckduckgo",
            "result_count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.exception("duckduckgo_web_search failed")
        return {"query": query, "source": "duckduckgo", "error": f"duckduckgo_web_search failed: {e}"}


async def _duckduckgo_web_search_async(query: str, max_results: int = 5) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_duckduckgo_web_search_sync, query, max_results),
            timeout=9.0,
        )
    except asyncio.TimeoutError:
        logger.warning("duckduckgo_web_search timed out after 9s")
        return {
            "query": query,
            "source": "duckduckgo",
            "error": "duckduckgo_web_search timed out after 9s",
        }


duckduckgo_web_search_tool = StructuredTool.from_function(
    func=_duckduckgo_web_search_sync,
    coroutine=_duckduckgo_web_search_async,
    name="duckduckgo_web_search",
    description=(
        "Search the public web for up-to-date information using DuckDuckGo and return concise results with links."
    ),
    args_schema=DuckDuckGoWebSearchInput,
)
