import hashlib
import os
import re
import sys
import threading
from datetime import datetime, timezone

import pandas as pd
from dotenv import dotenv_values, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.caches import InMemoryCache
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import AzureChatOpenAI
from loguru import logger

from .prompt import SYSTEM_TEMPLATE, AI_MESSAGE

# Remove default handler
logger.remove()

# Add custom handler with async writing
logger.add(
    sys.stderr,
    level="INFO",  # Set to "DEBUG" in development
    enqueue=True,  # Enable async logging
    backtrace=False,  # Disable traceback for better performance
    diagnose=False,  # Disable diagnosis for better performance
)


def clean_scraped_text(text: str) -> str:
    """
    Helper function to clean scraped text

    Args:
        text (str): scraped text

    Returns
        str: cleaned text
    """

    sentence = re.sub("'", "", text)  # Remove distracting single quotes
    sentence = re.sub(" +", " ", sentence)  # Replace extra spaces
    sentence = re.sub(r"\n: \'\'.*", "", sentence)  # Remove specific unwanted lines
    sentence = re.sub(r"\n!.*", "", sentence)
    sentence = re.sub(r"^:\'\'.*", "", sentence)
    sentence = re.sub(r"\n", " ", sentence)  # Replace non-breaking new lines with space
    sentence = re.sub("[^A-Za-z0-9 @]+", "", sentence)
    return sentence


def dataframe_to_text(df: pd.DataFrame) -> str:
    """
    Function to convert pandas dataframe (of scheme results) to cleaned text

    Args:
        df (pd.DataFrame): schemes in the user query for pandas dataframe

    Returns:
        str: cleaned text of information for each scheme
    """
    text_summary = ""
    for _, row in df.iterrows():
        # Handle both uppercase and lowercase column names
        scheme = row.get("scheme", "")
        agency = row.get("agency", "")
        description = row.get("llm_description", "")
        link = row.get("link", "")
        phone = row.get("phone", "")
        address = row.get("address", "")
        eligibility = row.get("eligibility", "")
        email = row.get("email", "")
        what_it_gives = row.get("what_it_gives", "")
        how_to_apply = row.get("how_to_apply", "")
        service_area = row.get("service_area", "")

        text_summary += f"Scheme Name: {scheme}, Agency: {agency}, Phone: {phone}, Address: {address}, Service Area: {service_area}, Eligibility: {eligibility}, Email: {email}, How to Apply: {how_to_apply}, What it Gives: {what_it_gives}, Description: {description}, Link: {link} \n"
    return text_summary


# TODO: get config from firebase
class Config:
    """Config class for loading .env file with chatbot API information"""

    def __init__(self):
        load_dotenv()

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr


class Chatbot:
    """Singleton-patterned class for managing chatbot API"""

    _instance = None

    llm = None

    _lock = threading.Lock()

    firebase_manager = None

    initialised = False

    @classmethod
    def initialise(cls):
        """Initialises the class by loading data from firestore, and loading pretrained models to Transformers"""

        if cls.initialised:
            return

        cls.db = cls.firebase_manager.firestore_client

        config = Config()

        try:
            cls.llm = AzureChatOpenAI(
                deployment_name=config.deployment,
                azure_endpoint=config.endpoint,
                openai_api_version=config.version,
                openai_api_key=config.apikey,
                openai_api_type=config.type,
                model_name=config.model,
                temperature=0.1,
                top_p=0.9,
                presence_penalty=0.2,
                frequency_penalty=0.2,
                max_tokens=512,
            )
            logger.info("Chatbot initialised")
        except Exception as e:  # TODO: logger
            logger.exception("LLM not initialized", e)

        cls.initialised = True

    def __new__(cls, firebase_manager: FirebaseManager):
        """Implementation of singleton pattern (returns initialised instance)"""

        if cls._instance is None:
            cls._instance = super(Chatbot, cls).__new__(cls)
            cls.firebase_manager = firebase_manager
            cls._instance.initialise()
        return cls._instance

    def __init__(self, firebase_manager: FirebaseManager):
        if not self.__class__.initialised:
            self.__class__.firebase_manager = firebase_manager
            self.__class__.initialise()

        # Initialize cache with a conservative size
        self.cache = InMemoryCache(maxsize=1000)  # Start with 1000 entries

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        Method to get session history of a conversation from Firestore.

        Args:
            session_id (str): session ID of conversation (same session id as original schemes search query)

        Returns:
            ChatMessageHistory: history of conversation
        """

        db = self.__class__.firebase_manager.firestore_client
        ref = db.collection("chatHistory").document(session_id)

        with self.__class__._lock:
            try:
                doc = ref.get()
                if doc.exists:
                    raw_data = doc.to_dict()
                    raw_messages = raw_data.get("messages", [])

                    messages = []
                    for msg in raw_messages:
                        if isinstance(msg, dict) and "role" in msg and "content" in msg:
                            if msg["role"] == "user":
                                messages.append(HumanMessage(content=msg["content"]))
                            elif msg["role"] == "assistant":
                                messages.append(AIMessage(content=msg["content"]))
                        elif isinstance(msg, str):
                            messages.append(AIMessage(content=msg))

                    return ChatMessageHistory(messages=messages)

                else:
                    initial_history = ChatMessageHistory(messages=[AIMessage(AI_MESSAGE)])
                    current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    ref.set(
                        {
                            "messages": [{"role": "assistant", "content": AI_MESSAGE}],
                            "last_updated": current_timestamp + " UTC",
                        }
                    )
                    return initial_history

            except Exception as e:
                logger.exception("Error fetching chat history from Firestore", e)
                return ChatMessageHistory(messages=[AIMessage(AI_MESSAGE)])

    def _generate_cache_key(self, query_text: str, input_text: str) -> str:
        """Generate a hashed cache key from query_text and input_text."""
        combined_text = f"{query_text}:{input_text}"
        return hashlib.sha256(combined_text.encode()).hexdigest()

    def chatbot(
        self, top_schemes_text: str, input_text: str, session_id: str, query_text: str
    ) -> dict[str, bool | str]:
        """
        Method called when sending message to chatbot

        Args:
            top_schemes_text (str): cleaned text containing information of top schemes for original user query
            input_text (str): message sent by user to chatbot
            session_id (str): session ID for conversation (matches session ID of schemes search query)
            query_text (str): text of the original query

        Returns:
            dict[str, bool | str]: a dictionary with 2 key-value pairs, first indicates the presence of a response from the chatbot, second contains the response (if any)
        """

        logger.info(f"Starting chatbot method for session {session_id}")

        # Define the LLM string identifier
        llm_string = "azure_openai_chatbot"

        # Generate hashed cache key
        cache_key = self._generate_cache_key(query_text, input_text)
        cached_response = self.cache.lookup(llm_string, cache_key)
        if cached_response:
            logger.info(f"Cache hit for query combination (key: {cache_key[:8]}...)")
            return {"response": True, "message": cached_response}

        template_text = SYSTEM_TEMPLATE.format(top_schemes=top_schemes_text)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", template_text),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}"),
            ]
        )

        chain = prompt_template | self.__class__.llm
        chain_with_history = RunnableWithMessageHistory(
            chain, self.get_session_history, input_messages_key="query", history_messages_key="history"
        )

        config = {"configurable": {"session_id": session_id}}
        message = chain_with_history.invoke({"query": input_text}, config=config)

        if message and message.content:
            # Cache the response with hashed key
            self.cache.update(llm_string, cache_key, message.content)
            results_json = {"response": True, "message": message.content}

            try:
                db = self.__class__.firebase_manager.firestore_client
                ref = db.collection("chatHistory").document(session_id)
                doc = ref.get()

                current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                if doc.exists:
                    chat_history = doc.to_dict().get("messages", [])
                    chat_history.append({"role": "user", "content": input_text})
                    chat_history.append({"role": "assistant", "content": message.content})
                    ref.set({"messages": chat_history, "last_updated": current_timestamp + " UTC"})
                else:
                    chat_history = [
                        {"role": "user", "content": input_text},
                        {"role": "assistant", "content": message.content},
                    ]
                    ref.set({"messages": chat_history, "last_updated": current_timestamp})
            except Exception as e:
                logger.exception("Error updating chat history in Firestore", e)

        else:
            results_json = {"response": False, "message": "No response from the chatbot."}

        return results_json

    def chatbot_stream(self, top_schemes_text: str, input_text: str, session_id: str, query_text: str):
        logger.info(f"Starting chatbot_stream method for session {session_id}")

        # Define the LLM string identifier
        llm_string = "azure_openai_chatbot"

        # Generate hashed cache key
        cache_key = self._generate_cache_key(query_text, input_text)
        cached_response = self.cache.lookup(llm_string, cache_key)
        if cached_response:
            logger.info(f"Cache hit for query combination (key: {cache_key[:8]}...)")
            yield cached_response
            return

        template_text = SYSTEM_TEMPLATE.format(top_schemes=top_schemes_text)

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", template_text),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}"),
            ]
        )

        chain = prompt_template | self.__class__.llm
        chain_with_history = RunnableWithMessageHistory(
            chain, self.get_session_history, input_messages_key="query", history_messages_key="history"
        )

        config = {"configurable": {"session_id": session_id}}

        full_response = ""  # Initialize full_response to accumulate streamed content

        # Use streaming
        for chunk in chain_with_history.stream({"query": input_text}, config=config):
            if hasattr(chunk, "content"):
                full_response += chunk.content  # Accumulate the content
                yield chunk.content

        # After streaming is complete, update chat history and cache
        try:
            db = self.__class__.firebase_manager.firestore_client
            ref = db.collection("chatHistory").document(session_id)
            doc = ref.get()

            current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if doc.exists:
                chat_history = doc.to_dict().get("messages", [])
                chat_history.append({"role": "user", "content": input_text})
                chat_history.append({"role": "assistant", "content": full_response})
                ref.set({"messages": chat_history, "last_updated": current_timestamp + " UTC"})

            # Cache the full response with hashed key
            self.cache.update(llm_string, cache_key, full_response)
            logger.info(f"Cached response with key: {cache_key[:8]}...")

        except Exception as e:
            logger.exception("Error updating chat history in Firestore", e)
