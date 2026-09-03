import os
from datetime import datetime, timezone
from uuid import uuid1
from typing import Any

import pandas as pd
from loguru import logger
from integrations import FirebaseManager
from .types import PredictParams
from .retriever import SearchModel


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
# LLM_SEARCH_RESULT_KEYS = ["scheme_type", "scheme_id", "agency", "image", "scheme_name", "summary", "description"]


class QueryHandler:
    """Core handler that delegates search to `SearchModel` (in retriever.py) and
    persists the agent's queries.
    """

    def __init__(self, firebase_manager: FirebaseManager):
        self.search_model = SearchModel(firebase_manager)
        self.__class__.firebase_manager = firebase_manager

    def _sanitize_for_firestore(self, data):
        """
        Sanitize data for Firestore by removing NaN/NaT values.
        """
        if isinstance(data, dict):
            return {k: self._sanitize_for_firestore(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_firestore(item) for item in data]
        elif isinstance(data, float) and pd.isna(data):
            return None
        elif pd.isna(data):
            return None
        elif isinstance(data, datetime):
            return int(data.timestamp())
        return data

    def save_llm_query(self, query: str, session_id: str, schemes_response: list[dict[str, str | int]]) -> None:
        """Save user query to firestore"""

        sanitized_response = self._sanitize_for_firestore(schemes_response)

        user_query = {
            "query_text": query,
            "query_timestamp": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "schemes_response": sanitized_response,
            "session_id": session_id,
        }

        try:
            # Add to the 'llmQuery' collection in firestore; the id is returned to the agent
            update_time, doc_ref = self.__class__.firebase_manager.firestore_client.collection("llmQuery").add(
                user_query
            )
            logger.info(f"Successfully saved session {session_id} to Firestore")
            return doc_ref.id
        except Exception as e:
            logger.exception(f"Failed to save session {session_id} to Firestore", e)
            raise e

    def predict_for_agent(self, params: PredictParams) -> dict[str, Any]:
        """Method to be called by agent for search tool.

        Returns up to the user's requested count of relevant schemes (the
        relevance floor always wins, so we never pad below it), and flags a
        shortfall when fewer relevant schemes exist than the user asked for so
        the agent can explain the gap.
        """

        final_results = self.search_model.aggregate_and_rank_results(
            params.query,
            params.similarity_threshold,
            params.requested_target,
        )

        session_id = params.session_id if params.session_id else str(uuid1())
        results_dict = final_results.to_dict(orient="records")

        doc_id = self.save_llm_query(params.query, session_id, results_dict)

        shortfall = params.requested_target is not None and len(results_dict) < params.requested_target

        results_json = {
            "session_id": session_id,
            "docID": doc_id,
            "data": results_dict,
            "requested_target": params.requested_target,
            "shortfall": shortfall,
            "mh": 0.7,
        }

        return results_json
