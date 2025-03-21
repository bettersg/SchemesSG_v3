import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict
from uuid import uuid1

import faiss
import numpy as np
import pandas as pd
import spacy
import torch
import torch.nn.functional as F
from fb_manager.firebaseManager import FirebaseManager
from loguru import logger
from pydantic import BaseModel

from transformers import AutoModel, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutputWithPooling

from google.cloud import firestore


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

parent_dir = Path(__file__).parent
model_path = parent_dir / "schemesv2-torch-allmpp-model"
tokenizer_path = parent_dir / "schemesv2-torch-allmpp-tokenizer"
embeddings_path = parent_dir / "schemesv2-your_embeddings.npy"
index_path = parent_dir / "schemesv2-your_index.faiss"
index_to_scheme_path = parent_dir / "index_to_scheme_id.json"


class PredictParams(BaseModel):
    """Parameters for search model (sent by client)"""

    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[int] = 0
    is_warmup: Optional[bool] = False  # Add flag for warmup requests


class SearchPreprocessor:
    """Class for text preprocesser for schemes search"""

    def __init__(self):
        self.nlp_spacy = spacy.load("en_core_web_sm")
        logger.info("Search Preprocessor initialised!")
        pass

    def extract_needs_based_on_conjunctions(self, sentence: str) -> list[str]:
        """
        Extract distinct needs based on coordinating conjunctions.

        Args:
            sentence (str): a sentence from the query

        Returns:
            list[str]: a list of phrases each corresponding to a need present in the query
        """

        doc = self.nlp_spacy(sentence)
        needs = []
        current_need_tokens = []

        for token in doc:
            # If the token is a coordinating conjunction (e.g., 'and') and not at the start of the sentence,
            # consider the preceding tokens as one distinct need.
            if token.text.lower() in ["and", "or"] and token.i != 0:
                if current_need_tokens:  # Ensure there's content before the conjunction
                    needs.append(" ".join([t.text for t in current_need_tokens]))
                    current_need_tokens = []  # Reset for the next need
            else:
                current_need_tokens.append(token)

        # Add the last accumulated tokens as a need, if any.
        if current_need_tokens:
            needs.append(" ".join([t.text for t in current_need_tokens]))

        return needs

    def split_into_sentences(self, text: str) -> list[str]:
        """
        Helper function to split the query into sentences

        Args:
            text (str): full query

        Returns:
            list[str]: full query split into a list of sentences
        """

        doc = self.nlp_spacy(text)
        return [sent.text.strip() for sent in doc.sents]

    def split_query_into_needs(self, query: str) -> list[str]:
        """
        Split the query into sentences and then extract needs focusing on conjunctions.

        Args:
            query (str): full user query

        Returns:
            list[str]: list of user needs found in the query
        """

        sentences = self.split_into_sentences(query)
        all_needs = []
        for sentence in sentences:
            needs_in_sentence = self.extract_needs_based_on_conjunctions(sentence)
            all_needs.extend(needs_in_sentence)

        return all_needs


class SearchModel:
    """Singleton-patterned class for schemes search model"""

    _instance = None

    db = None
    preprocessor = None

    model = None
    tokenizer = None
    embeddings = None
    index = None
    index_to_scheme_id = None

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
        cls.preprocessor = SearchPreprocessor()
        cls.model = AutoModel.from_pretrained(model_path)
        cls.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        cls.embeddings = np.load(embeddings_path)
        cls.index = faiss.read_index(str(index_path))  # Seems that faiss does not support pathlib
        # Load the FAISS index-to-scheme_id mapping
        with open(index_to_scheme_path, "r") as f:
            cls.index_to_scheme_id = json.load(f)
        cls.initialised = True

        logger.info("Search Model initialised!")

    def fetch_schemes_batch(self, scheme_ids: List[str]) -> List[Dict]:
        """Fetch multiple schemes"""
        # Create a cache key based on the scheme IDs
        scheme_cache_key = tuple(scheme_ids)

        # Check if the results are already in the cache
        if scheme_cache_key in self.query_cache:
            logger.info("Returning cached scheme details.")
            return self.query_cache[scheme_cache_key]

        # Get all documents in the collection
        docs = self.__class__.db.collection("schemes").where("__name__", "in", scheme_ids).get()

        # Process results
        scheme_details = []
        for doc in docs:
            scheme_data = doc.to_dict()
            scheme_data["scheme_id"] = doc.id
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

    @staticmethod
    def mean_pooling(model_output: BaseModelOutputWithPooling, attention_mask: torch.Tensor) -> torch.Tensor:
        """
        Mean Pooling - Take attention mask into account for correct averaging

        Args:
            model_output (BaseModelOutputWithPooling): embeddings of the query
            attention_mask (Tensor): attention mask used for mean pooling

        Returns:
            Tensor: mean-pooled tensor
        """

        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    # Now, you can use `index` for similarity searches with new user queries
    def search_similar_items(self, preproc: str, full_query: str, top_k: int) -> pd.DataFrame:
        """
        Searches for similar items in the FAISS index and returns a dataframe of schemes details and their similarity scores

        Args:
            preproc (str): preprocessed query (e.g. need or full query)
            full_query (str): the full query for logging purposes
            top_k (int): number of items to return

        Returns:
            pd.DataFrame: pandas dataframe containing scheme details and similarity scores
        """
        # Get the cache key
        query_cache_key = f"{preproc}_{top_k}"

        # Check if the results are already in the cache
        if query_cache_key in self.query_cache:
            logger.info("Returning cached search results.")
            return self.query_cache[query_cache_key]

        # Encode the query
        encoded_input = self.__class__.tokenizer([preproc], padding=True, truncation=True, return_tensors="pt")

        # Compute token embeddings
        with torch.no_grad():
            model_output = self.__class__.model(**encoded_input)

        # Perform pooling
        query_embedding = SearchModel.mean_pooling(model_output, encoded_input["attention_mask"])

        # Normalize embeddings
        query_embedding = F.normalize(query_embedding, p=2, dim=1)

        query_embedding = np.array(query_embedding).astype("float32")

        # Perform the search
        distances, indices = self.__class__.index.search(query_embedding, top_k)

        similarity_scores = np.exp(-distances)
        # similar_items = pd.DataFrame([df.iloc[indices[0]], distances[0], similarity_scores[0]])

        # Retrieve the scheme_ids using the FAISS indices
        retrieved_scheme_ids = []
        for idx in indices[0]:
            try:
                scheme_id = self.__class__.index_to_scheme_id[str(idx)]
                retrieved_scheme_ids.append(scheme_id)
            except KeyError:
                logger.warning(f"Index {idx} not found in index_to_scheme_id mapping, skipping.")
                # Continue with the rest of the indices

        # If we have no valid scheme IDs after filtering, return an empty DataFrame
        if not retrieved_scheme_ids:
            logger.warning("No valid scheme IDs found after filtering missing indices.")
            empty_df = pd.DataFrame(columns=["Scheme", "Agency", "Description", "scheme_id", "URL", "Similarity"])
            return empty_df

        try:
            scheme_details = self.fetch_schemes_batch(retrieved_scheme_ids)
        except Exception as e:
            logger.error(f"Error fetching schemes: {e}")
            raise

        # Convert to DataFrame
        scheme_df = pd.DataFrame(scheme_details)

        # If schemes were found, match with similarity scores
        if not scheme_df.empty:
            # Filter similarity scores to match retrieved schemes (excluding missing indices)
            # Create a mapping from original indices to the filtered position
            valid_indices = {}
            filtered_scores = []

            for i, idx in enumerate(indices[0]):
                idx_str = str(idx)
                if idx_str in self.__class__.index_to_scheme_id:
                    valid_indices[self.__class__.index_to_scheme_id[idx_str]] = i
                    filtered_scores.append(similarity_scores[0][i])

            # Map each scheme in scheme_df to its corresponding similarity score
            scheme_similarities = []
            for scheme_id in scheme_df["scheme_id"]:
                if scheme_id in valid_indices:
                    idx = valid_indices[scheme_id]
                    scheme_similarities.append(similarity_scores[0][idx])
                else:
                    # Fallback if for some reason scheme_id doesn't match
                    logger.warning(f"Scheme ID {scheme_id} not found in valid_indices mapping")
                    scheme_similarities.append(0.0)  # Default low similarity

            # Add similarity scores to the DataFrame
            results = pd.concat(
                [
                    scheme_df.reset_index(drop=True),
                    pd.DataFrame(scheme_similarities, columns=["Similarity"]).reset_index(drop=True),
                ],
                axis=1,
            )
        else:
            # If no schemes were found, return an empty DataFrame with the expected columns
            results = pd.DataFrame(columns=["Scheme", "Agency", "Description", "scheme_id", "URL", "Similarity"])

        # Add the query to the results and sort by similarity
        results["query"] = full_query
        results = results.sort_values(["Similarity"], ascending=False)

        # Store the results in the cache
        self.query_cache[query_cache_key] = results

        return results

    def combine_and_aggregate_results(
        self, needs: list[str], full_query: str, top_k: int, similarity_threshold: int
    ) -> pd.DataFrame:
        """
        Search for the appropriate scheme based on each of the user requirements (derived from their search query) and aggregate them into a pandas dataframe

        Args:
            needs (list[str]): preprocessed list of needs in user query
            full_query (str): original query text entered by user
            top_k (int): number of schemes returned
            similarity_threshold (int): minimum level of similarity a scheme needs to have to be returned

        Returns:
            pd.DataFrame: most suitable schemes for the query
        """

        # DataFrame to store combined results
        combined_results = None

        # Process each need
        for need in needs:
            # Get the results for the current need
            current_results = self.search_similar_items(need, full_query, top_k)

            # Initialize combined_results schema dynamically from the first result
            if combined_results is None:
                combined_results = pd.DataFrame(columns=current_results.columns)

            # Ensure consistent columns by reindexing current_results
            current_results = current_results.reindex(columns=combined_results.columns, fill_value=None)

            # Combine results
            combined_results = pd.concat([combined_results, current_results], ignore_index=True)

        # Drop duplicates and sort by similarity
        aggregated_results = combined_results.sort_values("Similarity", ascending=False).drop_duplicates(
            subset=["Scheme"]
        )

        # Filter by similarity threshold
        aggregated_results = aggregated_results[aggregated_results["Similarity"] >= similarity_threshold]

        # Create quintiles only if we have enough unique similarity scores
        unique_similarities = aggregated_results["Similarity"].nunique()
        if unique_similarities >= 5:
            aggregated_results["Quintile"] = pd.qcut(
                aggregated_results["Similarity"], q=5, labels=["1", "2", "3", "4", "5"]
            )
        else:
            # If we have less than 5 unique values, just rank them ordinally
            aggregated_results["Quintile"] = pd.Series(range(1, len(aggregated_results) + 1)).astype(str)

        # Return top_k results
        return aggregated_results.head(top_k)

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

        # Add to 'userQuery' collection in firestore with document name = session_id
        self.__class__.firebase_manager.firestore_client.collection("userQuery").document(session_id).set(user_query)

    def predict(self, params: PredictParams) -> dict[str, any]:
        """
        Main method to be called by endpoint handler

        Args:
            params (PredictParams): parameters given by user

        Returns:
            dict[str, any]: response containing session ID and schemes results based on query and other parameters
        """

        # Split search query into different requirements by the user
        split_needs = self.__class__.preprocessor.split_query_into_needs(params.query)

        # Searches the database for appropriate schemes per need and aggregates their overall suitability
        final_results = self.combine_and_aggregate_results(
            split_needs, params.query, params.top_k, params.similarity_threshold
        )

        session_id = str(uuid1())
        results_dict = final_results.to_dict(orient="records")

        # Skip saving to Firestore if this is a warmup request
        if not params.is_warmup:
            self.save_user_query(params.query, session_id, results_dict)

        results_json = {"sessionID": session_id, "data": results_dict, "mh": 0.7}

        return results_json
