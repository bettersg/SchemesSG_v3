import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid1

import chromadb
import pandas as pd
from fb_manager.firebaseManager import FirebaseManager
from langchain.docstore.document import Document
from langchain_community.retrievers import BM25Retriever
from langchain_openai import AzureOpenAIEmbeddings
from loguru import logger
from pydantic import BaseModel
from utils.pagination import decode_cursor, get_paginated_results


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

parent_dir = Path(__file__).parent
embeddings_path = parent_dir / "vector_store"


class PredictParams(BaseModel):
    """Parameters for search model (sent by client)"""

    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[int] = None
    is_warmup: Optional[bool] = False  # Add flag for warmup requests


class PaginatedSearchParams(BaseModel):
    """Parameters for paginated search (sent by client)"""

    query: str
    limit: Optional[int] = 20
    cursor: Optional[str] = None
    similarity_threshold: Optional[int] = None
    is_warmup: Optional[bool] = False
    top_k: Optional[int] = 100  # Number of items to retrieve from FAISS index
    filters: Optional[Dict[str, List[str]]] = {}


class SearchModel:
    """Singleton-patterned class for schemes search model"""

    _instance = None

    db = None
    embeddings = None
    index = None

    firebase_manager = None

    initialised = False

    # Add a cache to store query results
    query_cache = {}

    @classmethod
    def initialise(cls):
        """Initialises the class by loading data from firestore, and loading pretrained models to Transformers"""

        if cls.initialised:
            return

        cls.db = cls.firebase_manager.firestore_client
        # config = Config()
        # In SearchModel.initialise() method
        cls.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"],
            api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
            model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
        )
        chroma_client = chromadb.PersistentClient(path=embeddings_path)
        cls.index = chroma_client.get_collection("schemes")

        cls.initialised = True

    def fetch_schemes_batch(self, scheme_ids: List[str]) -> List[Dict]:
        """
        Fetch multiple schemes, batching to respect Firestore's 30-item 'in' limit, and remove 'scraped_text' field if present.

        Args:
            scheme_ids (List[str]): List of scheme IDs to fetch

        Returns:
            List[Dict]: List of scheme details as dictionaries
        """

        """"""
        # Create a cache key based on the scheme IDs
        scheme_cache_key = tuple(scheme_ids)

        # Check if the results are already in the cache
        if scheme_cache_key in self.query_cache:
            logger.info("Returning cached scheme details.")
            return self.query_cache[scheme_cache_key]

        # Helper to chunk scheme_ids into batches of 30
        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i : i + n]

        scheme_details = []
        for batch in chunk_list(scheme_ids, 30):
            docs = self.__class__.db.collection("schemes").where("__name__", "in", batch).get()
            for doc in docs:
                scheme_data = doc.to_dict()
                scheme_data["scheme_id"] = doc.id
                # Remove 'scraped_text' field if present
                if "scraped_text" in scheme_data:
                    del scheme_data["scraped_text"]
                scheme_details.append(scheme_data)

        # Store the results in the cache
        self.query_cache[scheme_cache_key] = scheme_details

        return scheme_details

    def __new__(cls, firebase_manager: FirebaseManager):
        """Implementation of singleton pattern (returns initialised instance)"""

        if cls._instance is None:
            cls._instance = super(SearchModel, cls).__new__(cls)
            cls.firebase_manager = firebase_manager
            # Initialize the instance (e.g., load models)
            cls._instance.initialise()
        return cls._instance

    def __init__(self, firebase_manager: FirebaseManager):
        if not self.__class__.initialised:
            self.__class__.firebase_manager = firebase_manager
            self.__class__.initialise()

    def search(self, query_text: str, top_k: int) -> pd.DataFrame:
        """
        Embed the input query, search the vector index for the most similar schemes,
        and return a merged DataFrame containing scheme metadata and similarity scores.

        Args:
            query_text (str): The user's search query.
            top_k (int): Maximum number of top-matching schemes to retrieve.

        Returns:
            pd.DataFrame: A DataFrame with columns:
                - scheme_id: Unique identifier of the scheme.
                - vec_similarity_score: Normalized vector similarity score (0–1).
                - query: The original query text.
                - Additional scheme metadata fetched from Firestore.

        Raises:
            Exception: Propagates any exception encountered while fetching scheme details,
                       after logging the error.
        """
        vec = self.__class__.embeddings.embed_query(query_text)
        results = self.__class__.index.query(query_embeddings=vec, n_results=top_k)

        distances, ids = results["distances"][0], results["ids"][0]

        # convert cosine distance → similarity and normalize
        vec_scores = [max(0, 1 - d) for d in distances]
        if max(vec_scores) > min(vec_scores):
            vec_scores = [(s - min(vec_scores)) / (max(vec_scores) - min(vec_scores)) for s in vec_scores]

        score_df = pd.DataFrame(zip(ids, vec_scores), columns=["scheme_id", "vec_similarity_score"])

        try:
            scheme_df = pd.DataFrame(self.fetch_schemes_batch(ids))
        except Exception as e:
            logger.error("Error fetching schemes: %s", e)
            raise

        merged = pd.merge(scheme_df, score_df, on="scheme_id")
        merged["query"] = query_text
        return merged

    def rank(self, query_text: str, results: pd.DataFrame) -> pd.DataFrame:
        """
        Apply BM25 ranking to the provided search results and compute combined scores.

        This method re-ranks the input results using the BM25 algorithm based on the
        textual content in the 'search_booster' column. It then merges the BM25 scores
        with the existing vector similarity scores, applying a weighted combination
        (70 % vector similarity, 30 % BM25) to produce a final ranking.

        NOTE: weighted combination
        is arbitrary and may need to be adjusted based on further explorations.

        Args:
            query_text (str): The user's search query used for BM25 relevance scoring.
            results (pd.DataFrame): A DataFrame containing at least:
                - 'scheme_id': Unique identifier for each scheme.
                - 'search_booster': Text content used for BM25 ranking.
                - 'vec_similarity_score': Pre-computed vector similarity score.

        Returns:
            pd.DataFrame: A new DataFrame sorted by 'combined_scores' in descending order,
                containing the original columns plus:
                - 'bm25_score': Computed BM25 relevance score (0–1).
                - 'combined_scores': Weighted sum of vector and BM25 scores.
        """
        docs = [
            Document(page_content=content, metadata={"id": sid})
            for sid, content in zip(results["scheme_id"], results["search_booster"])
        ]
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = len(docs)

        bm25_results = [
            (doc.metadata["id"], 1.0 - (i / retriever.k))
            for i, doc in enumerate(retriever.get_relevant_documents(query_text))
        ]
        bm25_df = pd.DataFrame(bm25_results, columns=["scheme_id", "bm25_score"])

        results = pd.merge(results, bm25_df, on="scheme_id", how="left")
        results["combined_scores"] = results["vec_similarity_score"] * 0.7 + results["bm25_score"].fillna(0) * 0.3
        return results.sort_values("combined_scores", ascending=False)

    def aggregate_and_rank_results(
        self, query_text: str, top_k: int, similarity_threshold: Optional[int]
    ) -> pd.DataFrame:
        """
        Perform hybrid vector + BM25 retrieval with caching.

        This method combines vector similarity search and BM25 text ranking to produce
        a ranked list of schemes. Results are cached by query and top_k to avoid
        redundant computation.

        Args:
            query_text (str): The user's search query.
            top_k (int): Maximum number of top-matching schemes to return.
            similarity_threshold (Optional[int]): Minimum similarity score required
                (currently unused; reserved for future filtering).

        Returns:
            pd.DataFrame: A DataFrame with at most `top_k` unique schemes, sorted by
                combined vector and BM25 scores in descending order.

        Notes:
            - The `similarity_threshold` parameter is accepted but not yet implemented.
            - Caching is keyed by `(query_text, top_k)` tuple.
        """
        cache_key = (query_text, top_k)
        if cache_key in self.query_cache:
            logger.debug("Cache hit for query '%s'", query_text)
            return self.query_cache[cache_key]

        results = self.search(query_text, top_k)
        results = self.rank(query_text, results).drop_duplicates("scheme_id")

        self.query_cache[cache_key] = results
        return results.head(top_k)

    def save_user_query(self, query: str, session_id: str, schemes_response: list[dict[str, str | int]]) -> None:
        """
        Save user query to firestore

        Args
            query (str): original query text send by user
            session_id (str): UUID for the query that is converted to string
            schemes_response (list[dict[str, str | int]]): schemes response converted to list of dictionaries
        """

        user_query = {
            "query_text": query,
            "query_timestamp": datetime.now(tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            "schemes_response": schemes_response,
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
            raise e  # Re-raise to ensure the calling code knows about the failure

    def predict(self, params: PredictParams) -> dict[str, any]:
        """
        Main method to be called by endpoint handler

        Args:
            params (PredictParams): parameters given by user

        Returns:
            dict[str, any]: response containing session ID and schemes results based on query and other parameters
        """

        # Searches the database for appropriate schemes per need and aggregates their overall suitability
        final_results = self.aggregate_and_rank_results(params.query, params.top_k, params.similarity_threshold)

        session_id = str(uuid1())
        results_dict = final_results.to_dict(orient="records")

        # Skip saving to Firestore if this is a warmup request
        if not params.is_warmup:
            self.save_user_query(params.query, session_id, results_dict)

        results_json = {"sessionID": session_id, "data": results_dict, "mh": 0.7}

        return results_json

    def predict_paginated(self, params: PaginatedSearchParams) -> dict[str, any]:
        """
        Method for paginated search results

        Args:
            params (PaginatedSearchParams): parameters given by user

        Returns:
            dict[str, any]: response containing paginated results
        """

        # Use the top_k parameter for FAISS index search
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
        complete_results = self.aggregate_and_rank_results(params.query, internal_top_k, params.similarity_threshold)

        filters = params.filters
        if filters:
            for field, criteria in filters.items():
                complete_results = complete_results[complete_results[field].isin(criteria)]

        # Convert to dict records for pagination
        complete_results_dict = complete_results.to_dict(orient="records")

        # Get paginated results with session ID
        page_results, next_cursor, has_more, total_count = get_paginated_results(
            complete_results_dict, limit=params.limit, cursor=params.cursor, session_id=session_id
        )

        # Skip saving to Firestore if this is a warmup request
        # Only save for first page to avoid redundant writes, but always save if it's a new session
        if not params.is_warmup and params.cursor is None:
            # Save session even if no results to ensure chat functionality works
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

        # Convert any Timestamp objects in results_json to strings
        def convert_timestamps_to_strings(obj):
            if isinstance(obj, dict):
                return {k: convert_timestamps_to_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamps_to_strings(elem) for elem in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        results_json = convert_timestamps_to_strings(results_json)

        return results_json
