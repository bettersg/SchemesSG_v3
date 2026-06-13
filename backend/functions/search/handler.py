import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid1

import pandas as pd
from integrations import FirebaseManager
from loguru import logger
from utils.pagination import decode_cursor, get_paginated_results

from .retriever import SearchModel
from .types import PaginatedSearchParams, PredictParams


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"
# LLM_SEARCH_RESULT_KEYS = ["scheme_type", "scheme_id", "agency", "image", "scheme_name", "summary", "description"]


# Convert any Timestamp objects in results_json to strings
def convert_timestamps_to_strings(obj):
    if isinstance(obj, dict):
        return {k: convert_timestamps_to_strings(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps_to_strings(elem) for elem in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class QueryHandler:
    """Core handler that delegates search to `SearchModel` (in retriever.py) and
    handles persistence/pagination concerns.
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

    def save_user_query(self, query: str, session_id: str, schemes_response: list[dict[str, str | int]]) -> None:
        """Save user query to firestore"""

        sanitized_response = self._sanitize_for_firestore(schemes_response)

        user_query = {
            "query_text": query,
            "query_timestamp": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "schemes_response": sanitized_response,
            "session_id": session_id,
        }

        try:
            # Add to 'userQuery' collection in firestore with document name = session_id
            self.__class__.firebase_manager.firestore_client.collection("userQuery").document(session_id).set(
                user_query
            )
            logger.info(f"Successfully saved session {session_id} to Firestore")
        except Exception as e:
            logger.exception(f"Failed to save session {session_id} to Firestore", e)
            raise e

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
            # Add to 'userQuery' collection in firestore with document name = session_id
            update_time, doc_ref = self.__class__.firebase_manager.firestore_client.collection("llmQuery").add(
                user_query
            )
            logger.info(f"Successfully saved session {session_id} to Firestore")
            return doc_ref.id
        except Exception as e:
            logger.exception(f"Failed to save session {session_id} to Firestore", e)
            raise e

    def predict(self, params: PredictParams) -> dict[str, Any]:
        """Main method to be called by endpoint handler"""

        final_results = self.search_model.aggregate_and_rank_results(
            params.query,
            requested_target=params.top_k,
        )

        session_id = str(uuid1())
        results_dict = final_results.to_dict(orient="records")

        if not params.is_warmup:
            self.save_user_query(params.query, session_id, results_dict)

        results_json = {"sessionID": session_id, "data": results_dict, "mh": 0.7}

        return results_json

    def predict_paginated(self, params: PaginatedSearchParams) -> dict[str, Any]:
        """Method for paginated search results"""

        # Use top_k as the maximum ranked result count before pagination.
        internal_top_k = params.top_k

        # Check if we have a cursor and extract session_id from it
        session_id = None
        if params.cursor:
            cursor_data = decode_cursor(params.cursor)
            if cursor_data and "session_id" in cursor_data:
                session_id = cursor_data.get("session_id")

        # Generate a new session ID if this is a fresh search
        if not session_id:
            session_id = str(uuid1())

        # Get complete results first (using top_k)
        complete_results = self.search_model.aggregate_and_rank_results(
            params.query,
            requested_target=internal_top_k,
        )

        filters = params.filters
        if filters:
            for field, criteria in filters.items():
                complete_results = complete_results[complete_results[field].isin(criteria)]

        # Convert to dict records for pagination
        complete_results_dict = complete_results.to_dict(orient="records")

        # Get paginated results with session ID
        page_results, next_cursor, has_more, total_count = get_paginated_results(
            complete_results_dict,
            limit=params.limit,
            cursor=params.cursor,
            session_id=session_id,
        )

        # Skip saving to Firestore if this is a warmup request
        if not params.is_warmup and params.cursor is None:
            results_to_save = page_results if page_results else []
            self.save_user_query(params.query, session_id, results_to_save)

        # Return the paginated results
        results_json = {
            "sessionID": session_id,
            "data": page_results,
            "total_count": total_count,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

        results_json = convert_timestamps_to_strings(results_json)

        return results_json

    def predict_for_agent(self, params: PredictParams) -> dict[str, Any]:
        """Method to be called by agent for search tool.

        Returns up to the user's requested count of ranked schemes, and flags a
        shortfall when fewer ranked schemes are available than the user asked
        for so the agent can explain the gap.
        """

        final_results = self.search_model.aggregate_and_rank_results(
            params.query,
            requested_target=params.requested_target,
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


if __name__ == "__main__":
    # Example usage
    fb_manager = FirebaseManager()
    # check if firebase_manager is initialized properly
    embeddings_docs = fb_manager.firestore_client.collection("schemes_embeddings").get()
    print(f"schemes_embeddings count: {len(embeddings_docs)}")
    handler = QueryHandler(fb_manager)
    params = PredictParams(
        query="What schemes are available for small businesses affected by COVID-19?",
        top_k=20,
        is_warmup=False,
    )
    response = handler.predict(params)
    print(response)
