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
from dotenv import dotenv_values, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import AzureChatOpenAI
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
        """
        Preprocesses text for schemes search model

        Args:
            sentence (str): sentence (need) to be preprocessed

        Returns:
            str: preprocessed text
        """

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

        return [self.preprocess(x) for x in all_needs]

# TODO: get config from firebase
class Config:
    def __init__(self):
        load_dotenv()

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr

class SearchModel:
    """Singleton-patterned class for schemes search model"""

    _instance = None

    preprocessor = None
    schemes_df = None

    model = None
    llm = None
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
        
        def init_chatbot(self):
            config = Config()
            return AzureChatOpenAI(
                        deployment_name=config.deployment,
                        azure_endpoint=config.endpoint,
                        openai_api_version=config.version,
                        openai_api_key=config.apikey,
                        openai_api_type=config.type,
                        model_name=config.model,
                        temperature=0.3
                    )

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

        global llm
        llm = init_chatbot()
        if not llm:
            print('llm not initialized')

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
    def search_similar_items(self, query_text: str, full_query: str, top_k: int) -> pd.DataFrame:
        """
        Searches database for schemes matching search query

        Args:
            query_text (str): specific need of user
            full_query (str): original query of user
            top_k (int): number of schemes returned

        Returns:
            pd.DataFrame: most suitable schemes for the query
        """

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
        """
        Save user query to firestore

        Args
            query (str): original query text send by user
            session_id (str): UUID for the query that is converted to string
            schemes_response (list[dict[str, str | int]]): schemes response converted to list of dictionaries
        """

        user_query = {
            "query_text": query,
            "query_timestamp": datetime.now(tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'),
            "schemes_response": schemes_response,
            "session_id": session_id
        }

        # Add to 'userQuery' collection in firestore with document name = session_id
        self.__class__.firebase_manager.firestore_client.collection('userQuery').document(session_id).set(user_query)


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

        self.save_user_query(params.query, session_id, results_dict)

        results_json = {
            "sessionId": session_id,
            "data": results_dict,
            "mh": 0.7
        }

        return results_json


    def get_session_history(self, session_id: str):
        global chat_history
        ai_message = """
        🌟 Welcome to Scheme Support Chat! 🌟 Feel free to ask me questions like:
        - "Can you tell me more about Scheme X?"
        - "How can I apply for support from Scheme X?"

        To get started, just type your question below. I'm here to help explore schemes results 🚀
        """
        if session_id not in chat_history:
            chat_history[session_id] = ChatMessageHistory(messages=[AIMessage(ai_message)])

        return chat_history[session_id]


    def chatbot(self, top_schemes_text: pd.DataFrame, input_text: str, session_id: str):
        global chat_history

        template_text = """
        As a virtual assistant, I'm dedicated to helping user navigate through the available schemes. User has done initial search based on their needs and system has provided top schemes relevant to the search. Now, my job is to advise on the follow up user queries based on the schemes data available by analyzing user query and extracting relevant answers from the top scheme data. Top Schemes Information includes scheme name, agency, Link to website, and may include text directly scraped from scheme website.

        In responding to user queries, I will adhere to the following principles:

        1. **Continuity in Conversation**: Each new question may build on the ongoing conversation. I'll consider the chat history to ensure a coherent and contextual dialogue.

        2. **Role Clarity**: My purpose is to guide user by leveraging the scheme information provided. My responses aim to advise based on this data, without undertaking any actions outside these confines.

        3. **Language Simplicity**: I commit to using simple, accessible English, ensuring my responses are understandable to all users, without losing the essence or accuracy of the scheme information.

        4. **Safety and Respect**: Maintaining a safe, respectful interaction is paramount. I will not entertain or generate harmful, disrespectful, or irrelevant content. Should any query diverge from the discussion on schemes, I will gently redirect the focus back to how I can assist with scheme-related inquiries.

        5. **Avoidance of Fabrication**: My responses will solely rely on the information from the scheme details provided, avoiding any speculative or unfounded content. I will not alter or presume any specifics not clearly indicated in the scheme descriptions.

        **Top Schemes Information:**
        """ + top_schemes_text

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", template_text),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}"),
            ]
        )

        chain = prompt_template | llm
        chain_with_history = RunnableWithMessageHistory(
                chain,
                self.get_session_history,
                input_messages_key="query",
                history_messages_key="history"
            )

        config = {'configurable': {'session_id': session_id}}
        message = chain_with_history.invoke({"query": input_text}, config=config)
        if message and message.content:
            results_json = {
                "response": True,
                "message": message.content
            }
        else:
            results_json = {
                "response": False,
                "message": "No response from the chatbot."
            }

        return results_json
