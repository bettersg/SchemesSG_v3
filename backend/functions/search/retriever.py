import os
from typing import Dict, List, Optional

import pandas as pd
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from loguru import logger
from integrations import FirebaseManager, EmbeddingsManager
from .scorers import rank_results, compute_vec_scores
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

# Collection for storing embeddings (separate from schemes collection)
EMBEDDINGS_COLLECTION = "schemes_embeddings"
SCHEMES_COLLECTION = "schemes"

# Search funnel tuning. We score essentially the whole candidate pool, then
# keep everything that clears the relevance bar. The result count is driven by
# relevance (and an optional user-requested target), not a fixed top-N. Values
# are starting points to be tuned against real queries.
#
# RETRIEVAL_LIMIT is a sentinel, not a result count: find_nearest returns at
# most the whole collection, so a value at/above the corpus size means
# "retrieve everything". 1000 is Firestore's hard maximum for find_nearest.limit
# and comfortably exceeds the current corpus, so it stands in for "all
# candidates". The relevance threshold (not this number) decides what's returned.
RETRIEVAL_LIMIT = 1000  # Firestore's max find_nearest limit; effectively "all candidates"
# Permissive relevance floor on the normalized combined score (0-1). It is not a
# precise relevance gate (embedding distances are too compressed for that without
# a reranker); empirically it keeps hundreds of results for a broad query and a
# focused handful for a specific one, while dropping the clearly-irrelevant tail.
# Ranking carries relevance; this only trims the tail. Tune against real queries.
RELEVANCE_THRESHOLD = 0.6
SAFETY_CEILING = 300  # hard upper bound on results returned, regardless of request
# How many top-ranked schemes the LLM reads to write its answer. The UI shows all
# relevant results (the user scrolls); the LLM only needs the top slice, which
# bounds per-turn token cost as the corpus grows.
LLM_RESULT_LIMIT = 50


def fetch_schemes_by_ids(firebase_manager: FirebaseManager, scheme_ids: List[str]) -> tuple[List[Dict], List[str]]:
    """Fetch schemes by Firestore document ID, preserving request order."""

    db = firebase_manager.firestore_client
    unique_scheme_ids = list(dict.fromkeys([scheme_id.strip() for scheme_id in scheme_ids if scheme_id.strip()]))
    scheme_details_by_id: dict[str, Dict] = {}

    for scheme_id in unique_scheme_ids:
        doc = db.collection(SCHEMES_COLLECTION).document(scheme_id).get()
        if not doc.exists:
            continue

        scheme_data = doc.to_dict()
        scheme_data["scheme_id"] = doc.id
        scheme_data.pop("scraped_text", None)
        scheme_details_by_id[scheme_id] = scheme_data

    scheme_details = [scheme_details_by_id[scheme_id] for scheme_id in unique_scheme_ids if scheme_id in scheme_details_by_id]
    missing_scheme_ids = [scheme_id for scheme_id in unique_scheme_ids if scheme_id not in scheme_details_by_id]

    return scheme_details, missing_scheme_ids


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
        cls.embeddings = EmbeddingsManager("text-embedding-3-large").model
        # Note: Vector search uses Firestore's findNearest() on schemes_embeddings collection
        # No separate index initialization needed - Firestore handles it

        cls.initialised = True

    def fetch_schemes_batch(self, scheme_ids: List[str]) -> List[Dict]:
        """
        Fetch multiple schemes, batching to respect Firestore's 30-item 'in' limit, and remove 'scraped_text' field if present.

        Args:
            scheme_ids (List[str]): List of scheme IDs to fetch

        Returns:
            List[Dict]: List of scheme details as dictionaries
        """

        # Create a cache key based on the scheme IDs
        scheme_cache_key = tuple(scheme_ids)
        # Check if the results are already in the cache
        if scheme_cache_key in self.query_cache:
            logger.info("Returning cached scheme details.")
            return self.query_cache[scheme_cache_key]

        scheme_details, _ = fetch_schemes_by_ids(self.__class__.firebase_manager, scheme_ids)

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

    def search(self, query_text: str, pool_size: Optional[int] = None) -> pd.DataFrame:
        """
        Embed the input query, search the Firestore vector index across the whole
        candidate pool, and return a merged DataFrame containing scheme metadata
        and the real cosine distance for each match.
        """
        if pool_size is None:
            pool_size = RETRIEVAL_LIMIT

        # Step 1: Generate query embedding
        vec = self.__class__.embeddings.embed_query(query_text)

        # Step 2: Query embeddings collection using Firestore vector search,
        # asking Firestore to return the actual cosine distance per match.
        # find_nearest returns at most the whole collection, so a sentinel limit
        # above the corpus size means "retrieve everything".
        embeddings_collection = self.__class__.db.collection(EMBEDDINGS_COLLECTION)
        vector_query = embeddings_collection.find_nearest(
            vector_field="embedding",
            query_vector=Vector(vec),
            distance_measure=DistanceMeasure.COSINE,
            limit=pool_size,
            distance_result_field="vector_distance",
        )

        # Get matching doc_ids and their real cosine distances from the results
        embedding_results = vector_query.get()
        ids = [doc.id for doc in embedding_results]
        distances = [doc.to_dict().get("vector_distance") for doc in embedding_results]

        if not ids:
            logger.warning(f"No vector search results for query: {query_text}")
            return pd.DataFrame(columns=["scheme_id", "vec_similarity_score", "query"])

        # Convert the real cosine distances into normalized relevance scores
        score_df = compute_vec_scores(ids, distances)

        # Step 3: Fetch full scheme data from schemes collection
        try:
            scheme_df = pd.DataFrame(self.fetch_schemes_batch(ids))
        except Exception as e:
            logger.error("Error fetching schemes: %s", e)
            raise

        if scheme_df.empty:
            logger.warning(f"No schemes found for doc_ids: {ids}")
            return pd.DataFrame(columns=["scheme_id", "vec_similarity_score", "query"])

        merged = pd.merge(scheme_df, score_df, on="scheme_id")
        merged["query"] = query_text
        return merged

    def rank(self, query_text: str, results: pd.DataFrame) -> pd.DataFrame:
        """
        Apply BM25 ranking to the provided search results and compute combined scores.
        """
        # Delegate ranking to the external ranker helper
        return rank_results(query_text, results)

    def aggregate_and_rank_results(
        self,
        query_text: str,
        threshold: Optional[float] = None,
        requested_target: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Perform hybrid vector + BM25 retrieval, then return a relevance-driven
        result set: every candidate whose combined score clears `threshold`,
        ordered best-first.

        `requested_target` is the count the user asked for (e.g. "20 healthcare
        schemes"). It caps the results, but the relevance floor always wins: we
        never pad below `threshold` to hit the number. When no target is given,
        all above-threshold results are returned. A hard `SAFETY_CEILING` always
        applies. The result count therefore varies with the query.
        """
        if threshold is None:
            threshold = RELEVANCE_THRESHOLD

        cap = SAFETY_CEILING if requested_target is None else min(requested_target, SAFETY_CEILING)

        cache_key = (query_text, threshold)
        if cache_key in self.query_cache:
            logger.debug("Cache hit for query '%s'", query_text)
            ranked = self.query_cache[cache_key]
        else:
            # Retrieve the full candidate pool, independent of how many we return.
            results = self.search(query_text)

            # Handle empty results - skip ranking if no vector results
            if results.empty:
                logger.warning(f"No search results to rank for query: {query_text}")
                self.query_cache[cache_key] = results
                return results

            ranked = self.rank(query_text, results).drop_duplicates("scheme_id")
            self.query_cache[cache_key] = ranked

        relevant = ranked[ranked["combined_scores"] >= threshold]
        return relevant.head(cap)
