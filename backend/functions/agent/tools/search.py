"""Search tool defined for agent use."""

import asyncio
import os
from typing import Any

# Import ToolRuntime from langgraph.prebuilt
from langgraph.prebuilt import ToolRuntime
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from search import PredictParams, QueryHandler
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging
from integrations import FirebaseManager

logger = setup_logging()

ACTION_MESSAGE_ON_START = 'Finding the top {top_k} schemes that best match "{query}"'
ACTION_MESSAGE_ON_END = 'Found {result_count} schemes matching "{query}".'
SHORT_ACTION_MESSAGE_ON_START = "Searching schemes database"
SHORT_ACTION_MESSAGE_ON_END = "{result_count} schemes found"
MINIMAL_LLM_KEYS = {"scheme", "agency", "summary"}


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
    # 1. REMOVED session_id from here so the LLM doesn't see or input it.

    # 2. Add config to allow arbitrary types so Pydantic handles ToolRuntime smoothly
    model_config = {"arbitrary_types_allowed": True}


def _search_schemes_sync(
    query: str,
    top_k: int = 30,
    runtime: ToolRuntime = None,  # 3. Added runtime parameter here
):
    logger.info("search_schemes tool invoked")
    top_k = max(10, min(int(top_k), 50))

    # 4. Extract session_id directly from the graph state via runtime
    session_id = None

    # Fallback option if session_id is stored in graph config instead of state:
    if runtime and runtime.config:
        session_id = runtime.config.get("configurable", {}).get("thread_id")

    try:
        write = get_stream_writer()
        write(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": SHORT_ACTION_MESSAGE_ON_START,
                    "message": ACTION_MESSAGE_ON_START.format(query=query, top_k=top_k),
                },
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit search input to stream: {e}")

    model = QueryHandler(FirebaseManager())
    params = PredictParams(
        query=query,
        top_k=top_k,
        is_warmup=False,
        session_id=session_id,  # Passes the extracted session_id here
    )
    results = model.predict_for_agent(params)
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": SHORT_ACTION_MESSAGE_ON_END.format(result_count=len(results.get("data", []))),
                    "message": ACTION_MESSAGE_ON_END.format(result_count=len(results.get("data", [])), query=query),
                },
            }
        )
        writer(
            {
                "type": "schemes_update",
                "data": {
                    "schemes": results.get("data", []),
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit search results to stream: {e}")

    # Sanitize results to only include minimal keys before returning to LLM, to avoid token overload and focus on relevant info
    schemes_response = results.get("data", [])
    schemes_response_dicts = []
    for scheme in schemes_response:
        schemes_response_dicts.append({k: v for k, v in scheme.items() if k in MINIMAL_LLM_KEYS})
    results["data"] = schemes_response_dicts

    return results


search_schemes_tool = StructuredTool.from_function(
    func=_search_schemes_sync,
    name="search_schemes",
    description=("Search for schemes relevant to the user's query. "),
    args_schema=SchemeSearchToolInput,
)
