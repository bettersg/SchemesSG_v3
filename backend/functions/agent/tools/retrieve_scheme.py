"""Retrieve full scheme details by scheme ID for agent use."""

from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from integrations import FirebaseManager
from search import fetch_schemes_by_ids
from utils.logging_setup import setup_logging


logger = setup_logging()

ACTION_MESSAGE_ON_START = "Searching our database for more information about selected schemes."
ACTION_MESSAGE_ON_END = "Retrieved detailed information for {result_count} schemes."
ACTION_MESSAGE_LABEL_ON_START = "Fetching scheme details"
ACTION_MESSAGE_LABEL_ON_END = "Scheme details found"


class RetrieveSchemesByIdsInput(BaseModel):
    scheme_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Firestore scheme IDs to retrieve detailed information for.",
    )


def _emit_action_message(label: str, message: str) -> None:
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": label,
                    "message": message,
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit retrieve scheme action message to stream: {e}")


def retrieve_schemes_by_ids(scheme_ids: list[str]) -> dict[str, Any]:
    logger.info("retrieve_schemes_by_ids tool invoked")
    normalized_scheme_ids = list(dict.fromkeys([scheme_id.strip() for scheme_id in scheme_ids if scheme_id.strip()]))

    _emit_action_message(ACTION_MESSAGE_LABEL_ON_START, ACTION_MESSAGE_ON_START)

    if not normalized_scheme_ids:
        _emit_action_message(ACTION_MESSAGE_LABEL_ON_END, ACTION_MESSAGE_ON_END.format(result_count=0))
        return {
            "schemes": [],
            "missing_scheme_ids": [],
            "result_count": 0,
        }

    schemes, missing_scheme_ids = fetch_schemes_by_ids(FirebaseManager(), normalized_scheme_ids)

    _emit_action_message(ACTION_MESSAGE_LABEL_ON_END, ACTION_MESSAGE_ON_END.format(result_count=len(schemes)))

    return {
        "schemes": schemes,
        "missing_scheme_ids": missing_scheme_ids,
        "result_count": len(schemes),
    }


retrieve_schemes_by_ids_tool = StructuredTool.from_function(
    func=retrieve_schemes_by_ids,
    name="retrieve_schemes_by_ids",
    description=(
        "Retrieve detailed information for one or more known schemes by scheme_id. "
        "Use this when the user asks for more details about specific schemes already found in the database."
    ),
    args_schema=RetrieveSchemesByIdsInput,
)
