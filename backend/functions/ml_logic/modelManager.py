import os
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid1

import faiss
import numpy as np
import pandas as pd
import spacy
import torch
import torch.nn.functional as F
from fb_manager.firebaseManager import FirebaseManager
from pydantic import BaseModel

from transformers import AutoModel, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutputWithPooling


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"


class PredictParams(BaseModel):
    """Parameters for search model (sent by client)"""

    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[int] = 0


class SearchPreprocessor:
    """Class for text preprocesser for schemes search"""

    def __init__(self):
        self.nlp_spacy = spacy.load("en_core_web_sm")
        print("Search Preprocessor initialised!")
        pass

    def preprocess(self, sentence: str) -> str:
        """Preprocesses text for schemes search model"""

        sentence = re.sub("'", "", sentence)  # Remove distracting single quotes
        sentence = re.sub(" +", " ", sentence)  # Replace extra spaces
        sentence = re.sub(r"\n: \'\'.*", "", sentence)  # Remove specific unwanted lines
        sentence = re.sub(r"\n!.*", "", sentence)
        sentence = re.sub(r"^:\'\'.*", "", sentence)
        sentence = re.sub(r"\n", " ", sentence)  # Replace non-breaking new lines with space

        # Tokenization and further processing with spaCy
        doc = self.nlp_spacy(sentence)
        tokens = []
        for token in doc:
            # Check if the token is a stopword or punctuation
            if token.is_stop or token.is_punct:
                continue
            # Check for numeric tokens or tokens longer than 2 characters
            if token.like_num or len(token.text) > 2:
                # Lemmatize (handling pronouns) and apply lowercase
                lemma = token.lemma_.lower().strip() if token.lemma_ != "-PRON-" else token.lower_
                tokens.append(lemma)

        # Further clean up to remove any introduced extra spaces
        processed_text = " ".join(tokens)
        processed_text = re.sub(" +", " ", processed_text)

        return processed_text

    def extract_needs_based_on_conjunctions(self, sentence: str) -> list[str]:
        """Extract distinct needs based on coordinating conjunctions."""

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
        """Helper function to split the query into sentences"""

        doc = self.nlp_spacy(text)
        return [sent.text.strip() for sent in doc.sents]

    def split_query_into_needs(self, query: str) -> list[str]:
        """Split the query into sentences and then extract needs focusing on conjunctions."""
        sentences = self.split_into_sentences(query)
        all_needs = []
        for sentence in sentences:
            needs_in_sentence = self.extract_needs_based_on_conjunctions(sentence)
            all_needs.extend(needs_in_sentence)

        return [self.preprocess(x) for x in all_needs]


class SearchModel:
    """Singleton-patterned class for schemes search model"""

    _instance = None

    preprocessor = None
    schemes_df = None

    model = None
    tokenizer = None
    embeddings = None
    index = None

    firebase_manager = None

    initialised = False

    @classmethod
    def initialise(cls):
        """Initialises the class by loading data from firestore, and loading pretrained models to Transformers"""

        if cls.initialised:
            return

        db = cls.firebase_manager.firestore_client
        schemes = db.collection("schemes").stream()

        cls.preprocessor = SearchPreprocessor()
        cls.schemes_df = pd.DataFrame([scheme.to_dict() for scheme in schemes])
        # pd.read_csv("ml_logic/schemes-updated-with-text.csv")

        cls.model = AutoModel.from_pretrained("ml_logic/schemesv2-torch-allmpp-model")
        cls.tokenizer = AutoTokenizer.from_pretrained("ml_logic/schemesv2-torch-allmpp-tokenizer")
        cls.embeddings = np.load("ml_logic/schemesv2-your_embeddings.npy")
        cls.index = faiss.read_index("ml_logic/schemesv2-your_index.faiss")
        cls.initialised = True

        print("Search Model initialised!")
        pass

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
        """Mean Pooling - Take attention mask into account for correct averaging"""

        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    # Now, you can use `index` for similarity searches with new user queries
    def search_similar_items(self, query_text: str, full_query: str, top_k: int) -> pd.DataFrame:
        """Searches database for schemes matching search query"""

        preproc = query_text

        # Tokenize text
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

        # Retrieve the most similar items
        similar_items = self.__class__.schemes_df.iloc[indices[0]][
            ["Scheme", "Agency", "Description", "Image", "Link", "Scraped Text", "What it gives", "Scheme Type"]
        ]

        results = pd.concat(
            [similar_items.reset_index(drop=True), pd.DataFrame(similarity_scores[0]).reset_index(drop=True)], axis=1
        )
        results = results.set_axis(
            [
                "Scheme",
                "Agency",
                "Description",
                "Image",
                "Link",
                "Scraped Text",
                "What it gives",
                "Scheme Type",
                "Similarity",
            ],
            axis=1,
        )
        results["query"] = full_query

        results = results.sort_values(["Similarity"], ascending=False)

        return results

    def combine_and_aggregate_results(
        self, needs: list[str], full_query: str, top_k: int, similarity_threshold: int
    ) -> pd.DataFrame:
        """Search for the appropriate scheme based on each of the user requirements (derived from their search query) and aggregate them into a pandas dataframe"""

        # DataFrame to store combined results
        combined_results = pd.DataFrame(
            columns=[
                "Scheme",
                "Agency",
                "Description",
                "Image",
                "Link",
                "Scraped Text",
                "What it gives",
                "Scheme Type",
                "Similarity",
                "query",
            ]
        )

        # Process each need
        for need in needs:
            # Get the results for the current need
            current_results = self.search_similar_items(need, full_query, top_k)
            # Combine with the overall results
            combined_results = pd.concat([combined_results, current_results], ignore_index=True)

        # Handle duplicates: Aggregate similarity for duplicates and drop duplicates
        aggregated_results = combined_results.groupby(
            [
                "Scheme",
                "Agency",
                "Description",
                "Image",
                "Link",
                "Scraped Text",
                "What it gives",
                "Scheme Type",
                "query",
            ],
            as_index=False,
        ).agg(
            {
                "Similarity": "sum"  # Adjust this function as needed to aggregate similarity scores appropriately
            }
        )

        # Calculate quintile thresholds
        quintile_thresholds = np.percentile(aggregated_results["Similarity"], [0, 20, 40, 60, 80, 100])
        # Assign quintile categories (0, 1, 2, 3, 4)
        # Since there are 5 thresholds (including 100th percentile), we specify 4 bins; pandas cuts into bins-1 categories
        aggregated_results["Quintile"] = pd.cut(
            aggregated_results["Similarity"], quintile_thresholds, labels=[0, 1, 2, 3, 4], include_lowest=True
        )

        # TODO add mental health model and increase the Similarity score

        # Filter out results that are below the minimum quintile threshold
        aggregated_results = aggregated_results[aggregated_results["Quintile"].astype(int) >= similarity_threshold]

        # Sort by similarity in descending order
        sorted_results = aggregated_results.sort_values(by="Similarity", ascending=False).reset_index(drop=True)

        return sorted_results

    def save_user_query(self, query: str, session_id: str, schemes_response: list[dict[str, str | int]]) -> None:
        """Save user query to firestore"""

        user_query = {
            "query_text": query,
            "query_timestamp": datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "schemes_response": schemes_response,
            "session_id": session_id
        }

        # Add to 'userQuery' collection in firestore
        self.__class__.firebase_manager.firestore_client.collection('userQuery').add(user_query)


    def predict(self, params: PredictParams) -> dict[str, any]:
        """Main method to be called by endpoint handler"""

        # Split search query into different requirements by the user
        split_needs = self.__class__.preprocessor.split_query_into_needs(params.query)

        # Searches the database for appropriate schemes per need and aggregates their overall suitability
        final_results = self.combine_and_aggregate_results(
            split_needs, params.query, params.top_k, params.similarity_threshold
        )

        session_id_uuid = uuid1()
        session_id = str(session_id_uuid)
        results_dict = final_results.to_dict(orient="records")

        self.save_user_query(params.query, session_id, results_dict)

        results_json = {
            "sessionId": session_id,
            "data": results_dict,
            "mh": 0.7
        }

        return results_json
