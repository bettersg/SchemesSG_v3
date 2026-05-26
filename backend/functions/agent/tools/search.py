"""Search tool defined for agent use."""

import asyncio
import os
from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from search import PaginatedSearchParams, QueryHandler
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging
from integrations import FirebaseManager

logger = setup_logging(level=os.getenv("AGENT_DEBUG_LOG_LEVEL", "DEBUG"))

ACTION_MESSAGE_ON_START = 'Finding the top {top_k} schemes that best match "{query}"'
ACTION_MESSAGE_ON_END = 'Found {result_count} schemes matching "{query}".'


class SchemeSearchToolInput(BaseModel):
    query: str = Field(
        ...,
        description="Natural language query about scheme eligibility, benefits, or requirements",
    )
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

    try:
        write = get_stream_writer()
        write(
            {
                "type": "action_message",
                "message": ACTION_MESSAGE_ON_START.format(query=query, top_k=top_k),
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit search input to stream: {e}")

    model = QueryHandler(FirebaseManager())
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
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "message": ACTION_MESSAGE_ON_END.format(result_count=len(results.get("data", [])), query=query),
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit search results to stream: {e}")

    return results


async def _search_schemes_async(query: str, top_k: int = 30) -> dict[str, Any]:
    logger.info("search_schemes async wrapper invoked")
    # Emit input to stream
    try:
        write = get_stream_writer()
        write(
            {
                "type": "action_message",
                "message": ACTION_MESSAGE_ON_START.format(query=query, top_k=top_k),
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit search input to stream: {e}")
    try:
        result = await asyncio.wait_for(asyncio.to_thread(_search_schemes_sync, query, top_k), timeout=8.0)
        return result
    except asyncio.TimeoutError:
        logger.warning("search_schemes timed out after 8s")
        return {"error": "search_schemes timed out after 8s"}
    except Exception as e:
        logger.exception("search_schemes failed")
        return {"error": f"search_schemes failed: {e}"}


search_schemes_tool = StructuredTool.from_function(
    func=_search_schemes_sync,
    coroutine=_search_schemes_async,
    name="search_schemes",
    description=("Search for schemes relevant to the user's query. "),
    args_schema=SchemeSearchToolInput,
)
