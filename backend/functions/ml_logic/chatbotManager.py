import os
import re
import threading

import pandas as pd
from dotenv import dotenv_values, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage
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
        cleanScrape = row["Scraped Text"]
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
    chat_history = {}

    firebase_manager = None

    initialised = False

    @classmethod
    def initialise(cls):
        """Initialises the class by loading data from firestore, and loading pretrained models to Transformers"""

        if cls.initialised:
            return

        config = Config()

        try:
            cls.llm = AzureChatOpenAI(
                deployment_name=config.deployment,
                azure_endpoint=config.endpoint,
                openai_api_version=config.version,
                openai_api_key=config.apikey,
                openai_api_type=config.type,
                model_name=config.model,
                temperature=0.3,
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
        Method to get session history of a conversation

        Args:
            session_id (str): session ID of conversation (same session id as original schemes search query)

        Returns
            ChatMessageHistory: history of conversation
        """

        ai_message = """
        🌟 Welcome to Scheme Support Chat! 🌟 Feel free to ask me questions like:
        - "Can you tell me more about Scheme X?"
        - "How can I apply for support from Scheme X?"

        To get started, just type your question below. I'm here to help explore schemes results 🚀
        """

        with self.__class__._lock:
            if session_id not in self.__class__.chat_history:
                self.__class__.chat_history[session_id] = ChatMessageHistory(messages=[AIMessage(ai_message)])

            return self.__class__.chat_history[session_id]

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
        As a virtual assistant, I'm dedicated to helping user navigate through the available schemes. User has done initial search based on their needs and system has provided top schemes relevant to the search. Now, my job is to advise on the follow up user queries based on the schemes data available by analyzing user query and extracting relevant answers from the top scheme data. Top Schemes Information includes scheme name, agency, Link to website, and may include text directly scraped from scheme website.

        In responding to user queries, I will adhere to the following principles:

        1. **Continuity in Conversation**: Each new question may build on the ongoing conversation. I'll consider the chat history to ensure a coherent and contextual dialogue.

        2. **Role Clarity**: My purpose is to guide user by leveraging the scheme information provided. My responses aim to advise based on this data, without undertaking any actions outside these confines.

        3. **Language Simplicity**: I commit to using simple, accessible English, ensuring my responses are understandable to all users, without losing the essence or accuracy of the scheme information.

        4. **Safety and Respect**: Maintaining a safe, respectful interaction is paramount. I will not entertain or generate harmful, disrespectful, or irrelevant content. Should any query diverge from the discussion on schemes, I will gently redirect the focus back to how I can assist with scheme-related inquiries.

        5. **Avoidance of Fabrication**: My responses will solely rely on the information from the scheme details provided, avoiding any speculative or unfounded content. I will not alter or presume any specifics not clearly indicated in the scheme descriptions.

        **Top Schemes Information:**
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
        else:
            results_json = {"response": False, "message": "No response from the chatbot."}

        return results_json
