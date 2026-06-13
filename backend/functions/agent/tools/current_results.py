"""Tools for deterministic refinement of the current scheme result set."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import StructuredTool
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from integrations import FirebaseManager
from search import MINIMAL_LLM_KEYS
from search.scorers import compute_bm25_scores
from utils.logging_setup import setup_logging


logger = setup_logging()

QUERY_COLLECTION_NAME = "llmQuery"
MAX_RESULT_LIMIT = 50

POSITION_START_MESSAGE = "Selecting the top {limit} schemes from the current results."
POSITION_END_MESSAGE = "Selected {result_count} schemes from the current results."
BM25_START_MESSAGE = 'Searching current results for "{query}".'
BM25_END_MESSAGE = 'Found {result_count} current results matching "{query}".'


class CurrentSchemesByPositionInput(BaseModel):
    doc_id: str = Field(
        ...,
        description="ID of the llmQuery document containing the current schemes list.",
    )
    limit: int = Field(
        ...,
        ge=1,
        le=MAX_RESULT_LIMIT,
        description="Number of already-ranked schemes to keep from the top of the current result list.",
    )


class CurrentSchemesBm25Input(BaseModel):
    doc_id: str = Field(
        ...,
        description="ID of the llmQuery document containing the current schemes list.",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="Keyword-style query to search within the current schemes list.",
    )
    limit: int = Field(
        10,
        ge=1,
        le=MAX_RESULT_LIMIT,
        description="Number of BM25-ranked matches to return. Use the user's exact count when they state one.",
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
        logger.debug(f"Failed to emit current-results action message to stream: {e}")


def _emit_schemes_update(schemes: list[dict[str, Any]]) -> None:
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "schemes_update",
                "data": {
                    "schemes": schemes,
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit current-results schemes update to stream: {e}")


def _sanitize_for_firestore(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_for_firestore(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_firestore(item) for item in value]
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())
    return value


def _retrieve_current_schemes(doc_id: str) -> list[dict[str, Any]]:
    try:
        doc = FirebaseManager().firestore_client.collection(QUERY_COLLECTION_NAME).document(doc_id).get()
    except Exception as e:
        logger.error(f"Error retrieving current schemes for doc_id {doc_id}: {e}")
        return []

    if not doc.exists:
        logger.warning(f"No current schemes document found for doc_id: {doc_id}")
        return []

    schemes = doc.to_dict().get("schemes_response", [])
    if not isinstance(schemes, list):
        return []

    return [scheme for scheme in schemes if isinstance(scheme, dict)]


def _save_current_schemes_result(
    *,
    source_doc_id: str,
    query_text: str,
    schemes: list[dict[str, Any]],
) -> str | None:
    try:
        _, doc_ref = FirebaseManager().firestore_client.collection(QUERY_COLLECTION_NAME).add(
            {
                "query_text": query_text,
                "query_timestamp": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "schemes_response": _sanitize_for_firestore(schemes),
                "source_doc_id": source_doc_id,
            }
        )
        return doc_ref.id
    except Exception as e:
        logger.error(f"Error saving current schemes result for doc_id {source_doc_id}: {e}")
        return None


def _slim_for_llm(schemes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in scheme.items() if k in MINIMAL_LLM_KEYS} for scheme in schemes]


def _stringify_for_search(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_stringify_for_search(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_stringify_for_search(item) for item in value.values())
    return str(value)


def _scheme_bm25_document(scheme: dict[str, Any]) -> str:
    fields = [
        "scheme",
        "scheme_name",
        "agency",
        "summary",
        "description",
        "llm_description",
        "eligibility",
        "how_to_apply",
        "search_booster",
        "desc_booster",
        "who_is_it_for",
        "what_it_gives",
        "scheme_type",
        "benefits",
        "target_audience",
    ]
    return " ".join(_stringify_for_search(scheme.get(field)) for field in fields)


def select_current_schemes_by_position(doc_id: str, limit: int) -> dict[str, Any]:
    """Keep the first N schemes from the saved ranked result list."""

    limit = max(1, min(int(limit), MAX_RESULT_LIMIT))
    _emit_action_message("Selecting top schemes", POSITION_START_MESSAGE.format(limit=limit))

    schemes = _retrieve_current_schemes(doc_id)
    selected = schemes[:limit]
    result_doc_id = _save_current_schemes_result(
        source_doc_id=doc_id,
        query_text=f"top {limit} current schemes",
        schemes=selected,
    )

    _emit_action_message("Schemes selected", POSITION_END_MESSAGE.format(result_count=len(selected)))
    _emit_schemes_update(selected)

    return {
        "docID": result_doc_id,
        "schemes": _slim_for_llm(selected),
        "result_count": len(selected),
    }


def search_current_schemes_bm25(doc_id: str, query: str, limit: int) -> dict[str, Any]:
    """Keyword-search the saved result list with BM25, then return the top N."""

    query = query.strip()
    limit = max(1, min(int(limit), MAX_RESULT_LIMIT))
    _emit_action_message("Searching current schemes", BM25_START_MESSAGE.format(query=query))

    schemes = _retrieve_current_schemes(doc_id)
    documents = [_scheme_bm25_document(scheme) for scheme in schemes]
    scores = compute_bm25_scores(query, documents)

    ranked = sorted(
        [
            (index, score, scheme)
            for index, (score, scheme) in enumerate(zip(scores, schemes))
            if score > 0
        ],
        key=lambda item: (-item[1], item[0]),
    )
    selected = [scheme | {"bm25_score": score} for _, score, scheme in ranked[:limit]]
    result_doc_id = _save_current_schemes_result(
        source_doc_id=doc_id,
        query_text=query,
        schemes=selected,
    )

    _emit_action_message("Current schemes matched", BM25_END_MESSAGE.format(result_count=len(selected), query=query))
    _emit_schemes_update(selected)

    return {
        "docID": result_doc_id,
        "schemes": _slim_for_llm(selected),
        "result_count": len(selected),
        "query": query,
    }


select_current_schemes_by_position_tool = StructuredTool.from_function(
    func=select_current_schemes_by_position,
    name="select_current_schemes_by_position",
    description=(
        "Keep the top N schemes from the current already-ranked results without semantic filtering. "
        "Use this only for positional requests such as 'top 3', 'first 5', or 'show fewer results'."
    ),
    args_schema=CurrentSchemesByPositionInput,
)

search_current_schemes_bm25_tool = StructuredTool.from_function(
    func=search_current_schemes_bm25,
    name="search_current_schemes_bm25",
    description=(
        "Search within the current saved scheme results using BM25 keyword matching, then return the top N matches. "
        "Use this for refinement by a topic or criterion inside existing results, such as medication-based support."
    ),
    args_schema=CurrentSchemesBm25Input,
)
