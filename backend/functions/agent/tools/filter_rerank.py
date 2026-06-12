"""Tool to reorder/filter an existing schemes list using LLM-provided indices."""

import asyncio
import json
from typing import Any
from datetime import datetime, timezone

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field
from utils.logging_setup import setup_logging
from integrations import FirebaseManager, LLMManager


logger = setup_logging()
# To be used as a fallback message if LLM doesn't provide an action_message in the tool call input.
ACTION_MESSAGE_ON_START = "Filtering and re-ranking existing schemes.\n Instructions are: \n {directive}"
ACTION_MESSAGE_ON_END = "Filtered and re-ranked schemes list to {num_items} items."
SHORT_ACTION_MESSAGE_ON_START = "Filtering schemes"
SHORT_ACTION_MESSAGE_ON_END = "Schemes filtered"
MINIMAL_LLM_KEYS = {"scheme", "agency", "summary"}

QUERY_COLLECTION_NAME = "llmQuery"
MODEL_NAME = "gpt-5.4-mini"
RERANKER_COLLECTION_NAME = "filterRerankResults"


class FilterRerankInput(BaseModel):
    doc_id: str = Field(
        ...,
        description="ID of the document containing the schemes list to filter/rerank. This should be provided in the current context for the tool to access.",
    )
    directive: str = Field(
        ...,
        description="Instructions for how to filter/rerank the schemes list. Be specific about criteria and desired outcome.",
    )


RERANKER_TEMPLATE = """
You are provided a list of schemes in JSON format.
{schemes_json}
Your task is to filter and rerank this list based on the following directive:
{directive}
Return a JSON array of zero-based indices representing the new order and selection of schemes that best fulfills the directive.
Only include indices of schemes that meet the criteria, and order them according to the directive. Do not include any indices of schemes that should be excluded based on the directive.
"""


def _retrieve_search_results_by_doc_id(doc_id: str) -> str:
    """Fetch the schemes list JSON string from the database using the provided document ID."""
    try:
        firebase_manager = FirebaseManager()
        print(f"Retrieving schemes context for doc_id: {doc_id}")
        doc_ref = firebase_manager.firestore_client.collection(QUERY_COLLECTION_NAME).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("schemes_response", [])
        else:
            logger.warning(f"No document found for doc_id: {doc_id}")
            return ""
    except Exception as e:
        logger.error(f"Error retrieving schemes list for doc_id {doc_id}: {e}")
        return ""


def _filter_rerank(
    schemes_dict: str,
    directive: str,
) -> dict[str, Any]:
    llm_manager = LLMManager(MODEL_NAME)
    llm_manager.modify_llm(
        **{
            "temperature": 0.0,
            "max_tokens": 500,
        }
    )
    llm = llm_manager.get_llm()
    llm_response = llm.invoke(RERANKER_TEMPLATE.format(schemes_json=json.dumps(schemes_dict), directive=directive))
    llm_text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

    try:
        indices = json.loads(llm_text.strip())
        if not isinstance(indices, list) or not all(isinstance(i, int) for i in indices):
            raise ValueError("LLM response is not a list of integers.")
    except Exception as e:
        logger.error(f"Error parsing LLM response for filter_rerank: {e}")
        return {"error": f"Failed to parse LLM response: {e}", "llm_response": llm_text}
    return {"indices": indices, "llm_response": llm_text}


def _sort_json_array_by_indices(schemes_dict: list, indices: list[int]) -> str:
    try:
        data = schemes_dict
        if not isinstance(data, list):
            raise ValueError("Input JSON is not an array.")
        sorted_data = [data[i] for i in indices if 0 <= i < len(data)]
        return sorted_data
    except Exception as e:
        logger.error(f"Error sorting JSON array by indices: {e}")
        return []


def _save_filtered_reranked_schemes(doc_id: str, schemes: list) -> None:
    """Save the filtered and reranked schemes list back to the database under the same document ID."""
    try:
        firebase_manager = FirebaseManager()
        _, doc_ref = firebase_manager.firestore_client.collection(RERANKER_COLLECTION_NAME).add(
            {
                "llmquery_doc_id": doc_id,
                "schemes_response": schemes,
                "filter_rerank_timestamp": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            }
        )
        logger.info(
            f"Successfully saved filtered/reranked schemes for doc_id {doc_id} to Firestore with new doc_id {doc_ref.id}"
        )
        return doc_ref.id
    except Exception as e:
        logger.error(f"Error saving filtered/reranked schemes for doc_id {doc_id} to Firestore: {e}")
        return None


def filter_rerank_by_directive(
    doc_id: str,
    directive: str,
) -> dict[str, Any]:
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": SHORT_ACTION_MESSAGE_ON_START,
                    "message": ACTION_MESSAGE_ON_START.format(directive=directive),
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit filter/rerank start message to stream: {e}")
    schemes_dict = _retrieve_search_results_by_doc_id(doc_id)
    if not schemes_dict:
        return {"error": "No schemes context found for the provided doc_id."}

    result = _filter_rerank(schemes_dict, directive)
    if result.get("error"):
        return {"error": result["error"], "llm_response": result.get("llm_response", "")}
    indices = result.get("indices", [])
    sorted_schemes = _sort_json_array_by_indices(schemes_dict, indices)
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": SHORT_ACTION_MESSAGE_ON_END,
                    "message": ACTION_MESSAGE_ON_END.format(num_items=len(sorted_schemes)),
                },
            }
        )
        writer(
            {
                "type": "schemes_update",
                "data": {
                    "schemes": sorted_schemes,
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit filter/rerank completion message to stream: {e}")
    new_doc_id = _save_filtered_reranked_schemes(doc_id, sorted_schemes)
    sorted_schemes_dicts = []
    for scheme in sorted_schemes:
        sorted_schemes_dicts.append({k: v for k, v in scheme.items() if k in MINIMAL_LLM_KEYS})
    return {
        "filtered_reranked_doc_id": new_doc_id,
        "schemes": sorted_schemes_dicts,
        "llm_response": result.get("llm_response", ""),
    }


filter_rerank_by_directive_tool = StructuredTool.from_function(
    func=filter_rerank_by_directive,
    name="filter_rerank_by_directive",
    description=(
        "Filter and reorder an existing schemes list based on a natural language directive. "
        "The tool retrieves the current schemes list using the provided document ID, then uses the directive to determine how to filter and reorder the schemes. "
        "The directive should clearly specify the criteria for filtering and the desired order of the schemes."
    ),
    args_schema=FilterRerankInput,
)
