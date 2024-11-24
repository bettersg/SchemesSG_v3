import os
import re
import threading
from datetime import datetime, timezone

import pandas as pd
from dotenv import dotenv_values, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import AzureChatOpenAI
from loguru import logger


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
        cleanScrape = row["scraped_text"]
        sentence = clean_scraped_text(cleanScrape)

        text_summary += f"Scheme Name: {row['Scheme']}, Agency: {row['Agency']}, Description: {row['Description']}, Link: {row['Link']}, Scraped Text from website: {sentence}\n"
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

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        Method to get session history of a conversation from Firestore.

        Args:
            session_id (str): session ID of conversation (same session id as original schemes search query)

        Returns:
            ChatMessageHistory: history of conversation
        """

        ai_message = """
        🌟 Welcome to Scheme Support Chat! 🌟 Feel free to ask me questions like:
        - "Can you tell me more about Scheme X?"
        - "How can I apply for support from Scheme X?"

        To get started, just type your question below. I'm here to help explore schemes results 🚀
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
                    initial_history = ChatMessageHistory(messages=[AIMessage(ai_message)])
                    current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    ref.set({
                        "messages": [
                            {"role": "assistant", "content": ai_message}
                        ],
                        "last_updated": current_timestamp + " UTC"
                    })
                    return initial_history

            except Exception as e:
                logger.exception("Error fetching chat history from Firestore", e)
                return ChatMessageHistory(messages=[AIMessage(ai_message)])


    def chatbot(self, top_schemes_text: str, input_text: str, session_id: str) -> dict[str, bool | str]:
        """
        Method called when sending message to chatbot

        Args:
            top_schemes_text (str): cleaned text containing information of top schemes for original user query
            input_text (str): message sent by user to chatbot
            session_id (str): session ID for conversation (matches session ID of schemes search query)

        Returns:
            dict[str, bool | str]: a dictionary with 2 key-value pairs, first indicates the presence of a response from the chatbot, second contains the response (if any)
        """

        template_text = (
            """
            I’m a virtual assistant designed to help users explore schemes based on their needs. The user has already received top schemes relevant to their search. My role is to answer follow-up queries by analyzing and extracting insights from the provided scheme data, which includes the scheme name, agency, link to the website, and potentially text scraped from the scheme website.
            Guidelines for my responses:
                1.	Contextual Answers: I’ll consider the chat history to ensure coherent, contextual answers.
                2.	Data-Driven Guidance: My role is to provide advice based on the scheme data only, staying within its scope.
                3.	Clear Communication: I’ll use simple, clear English while preserving the accuracy of the scheme details.
                4.	Respect and Focus: I’ll keep interactions respectful and safe, redirecting to scheme-related topics if the conversation diverges.
                5.	No Speculation: My responses will strictly rely on the given scheme details, avoiding fabrication or assumptions.
            """
            + top_schemes_text
        )

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
                    ref.set({
                        "messages": chat_history,
                        "last_updated": current_timestamp + " UTC"
                    })
                else:
                    chat_history = [
                        {"role": "user", "content": input_text},
                        {"role": "assistant", "content": message.content},
                    ]
                    ref.set({
                        "messages": chat_history,
                        "last_updated": current_timestamp
                    })
            except Exception as e:
                logger.exception("Error updating chat history in Firestore", e)

        else:
            results_json = {"response": False, "message": "No response from the chatbot."}

        return results_json

    def chatbot_stream(self, top_schemes_text: str, input_text: str, session_id: str):
        """Streaming version of the chatbot method"""
        template_text = (
            """
            I’m a virtual assistant designed to help users explore schemes based on their needs. The user has already received top schemes relevant to their search. My role is to answer follow-up queries by analyzing and extracting insights from the provided scheme data, which includes the scheme name, agency, link to the website, and potentially text scraped from the scheme website.
            Guidelines for my responses:
                1.	Contextual Answers: I’ll consider the chat history to ensure coherent, contextual answers.
                2.	Data-Driven Guidance: My role is to provide advice based on the scheme data only, staying within its scope.
                3.	Clear Communication: I’ll use simple, clear English while preserving the accuracy of the scheme details.
                4.	Respect and Focus: I’ll keep interactions respectful and safe, redirecting to scheme-related topics if the conversation diverges.
                5.	No Speculation: My responses will strictly rely on the given scheme details, avoiding fabrication or assumptions.
            """
            + top_schemes_text
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", template_text),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{query}"),
        ])

        chain = prompt_template | self.__class__.llm
        chain_with_history = RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="query",
            history_messages_key="history"
        )

        config = {"configurable": {"session_id": session_id}}

        # Use streaming
        for chunk in chain_with_history.stream(
            {"query": input_text},
            config=config
        ):
            if hasattr(chunk, 'content'):
                yield chunk.content

        # After streaming is complete, update chat history
        try:
            db = self.__class__.firebase_manager.firestore_client
            ref = db.collection("chatHistory").document(session_id)
            doc = ref.get()

            current_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            if doc.exists:
                chat_history = doc.to_dict().get("messages", [])
                chat_history.append({"role": "user", "content": input_text})
                chat_history.append({"role": "assistant", "content": full_response})
                ref.set({
                    "messages": chat_history,
                    "last_updated": current_timestamp + " UTC"
                })
        except Exception as e:
            logger.exception("Error updating chat history in Firestore", e)
