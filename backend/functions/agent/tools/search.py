"""Search tool defined for agent use."""

from integrations import FirebaseManager
from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from langgraph.prebuilt import ToolRuntime
from pydantic import BaseModel, Field
from search import LLM_RESULT_LIMIT, PredictParams, QueryHandler, slim_for_llm
from utils.logging_setup import setup_logging


logger = setup_logging()

ACTION_MESSAGE_ON_START = 'Finding the schemes that best match "{query}"'
ACTION_MESSAGE_ON_END = 'Found {result_count} schemes matching "{query}".'
SHORT_ACTION_MESSAGE_ON_START = "Searching schemes database"
SHORT_ACTION_MESSAGE_ON_END = "{result_count} schemes found"


class SchemeSearchToolInput(BaseModel):
    query: str = Field(
        ...,
        description="Natural language query about scheme eligibility, benefits, or requirements",
    )
    requested_count: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Leave this UNSET for almost every query. The search already returns a "
            "ranked result set on its own. ONLY set a number when the user "
            "themselves states an explicit quantity in their message, e.g. "
            "'show me 20 healthcare schemes' -> 20, 'give me 5 options' -> 5. "
            "Do NOT set it for an ordinary request like 'I need health support' "
            "or to pick a 'reasonable' count yourself."
        ),
    )
    # 1. REMOVED session_id from here so the LLM doesn't see or input it.

    # 2. Add config to allow arbitrary types so Pydantic handles ToolRuntime smoothly
    model_config = {"arbitrary_types_allowed": True}


def _search_schemes_sync(
    query: str,
    requested_count: int | None = None,
    runtime: ToolRuntime = None,  # 3. Added runtime parameter here
):
    logger.info("search_schemes tool invoked")
    requested_target = int(requested_count) if requested_count else None

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
                    "message": ACTION_MESSAGE_ON_START.format(query=query),
                },
            },
        )
    except Exception as e:
        logger.debug(f"Failed to emit search input to stream: {e}")

    model = QueryHandler(FirebaseManager())
    params = PredictParams(
        query=query,
        requested_target=requested_target,
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

    # The UI already received the ranked scheme set via the schemes_update
    # stream above. The LLM only reads the top slice with minimal keys, to keep
    # the answer focused and bound per-turn token cost.
    results["data"] = slim_for_llm(results.get("data", []), LLM_RESULT_LIMIT)

    return results


search_schemes_tool = StructuredTool.from_function(
    func=_search_schemes_sync,
    name="search_schemes",
    description=("Search for schemes relevant to the user's query. "),
    args_schema=SchemeSearchToolInput,
)
