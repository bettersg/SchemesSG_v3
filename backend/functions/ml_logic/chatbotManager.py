"""
Query text not included in the context.
LLM unable to answer questions like which scheme is suitable for me.
"""

import os

from dotenv import find_dotenv, load_dotenv
from fb_manager.firebaseManager import FirebaseManager
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy
from utils.logging_setup import setup_logging

from .cache import InMemoryCacheWithMaxsize, generate_cache_key
from .config import PROVIDER_MODEL_NAME, ChatbotConfig
from .firestore_saver import FirestoreChatSaver
from .prompt import SYSTEM_TEMPLATE
from .states import ChatbotState

load_dotenv(find_dotenv())

logger = setup_logging()


class Chatbot:
    """Singleton-patterned class for managing chatbot API"""

    _instance = None

    llm = None

    firebase_manager = None

    initialised = False

    @classmethod
    def initialise(cls):
        """Initialises the class by loading data from firestore, and loading pretrained models to Transformers"""

        if cls.initialised:
            return

        cls.db = cls.firebase_manager.firestore_client

        chatbot_config = ChatbotConfig()

        try:
            cls.llm = init_chat_model(
                PROVIDER_MODEL_NAME,
                azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                **chatbot_config.__dict__,
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
        # ! Should the cache be a global cache?
        self.cache = InMemoryCacheWithMaxsize(maxsize=1000)
        self.initialise_graph()

    def initialise_graph(self):
        graph_builder = StateGraph(ChatbotState)
        memory = FirestoreChatSaver(client=self.db)
        graph_builder.add_node("chatbot", self.call_chat_llm, cache_policy=CachePolicy(key_func=generate_cache_key))
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)
        self.graph = graph_builder.compile(checkpointer=memory, cache=self.cache)

    def call_chat_llm(self, state: ChatbotState) -> dict:
        system_message = SystemMessage(content=SYSTEM_TEMPLATE.format(top_schemes=state["top_schemes_text"]))
        response = self.llm.invoke([{"role": "system", "content": system_message.content}] + state["messages"])
        return {"messages": [response]}

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

        config = self._create_configurable(session_id)

        try:
            response = self.graph.invoke(
                {
                    "messages": [{"role": "user", "content": input_text}],
                    "top_schemes_text": top_schemes_text,
                    "query_text": query_text,
                },
                config=config,
                stream_mode="updates",
            )
            message_content = response[0]["chatbot"]["messages"][0].content
            results_json = {"response": True, "message": message_content}

        except Exception as e:
            logger.exception("Error in chatbot invocation", e)
            results_json = {"response": False, "message": "No response from the chatbot."}

        return results_json

    def chatbot_stream(self, top_schemes_text: str, input_text: str, session_id: str, query_text: str):
        logger.info(f"Starting chatbot_stream method for session {session_id}")
        config = self._create_configurable(session_id)
        stream = self.graph.stream(
            {
                "messages": [{"role": "user", "content": input_text}],
                "top_schemes_text": top_schemes_text,
                "query_text": query_text,
            },
            config=config,
            stream_mode=["messages", "updates"],
        )
        cached = True
        saved_updates = None
        for mode, data in stream:
            if mode == "messages":
                cached = False
                message_chunk, _ = data
                yield message_chunk.content
            else:
                saved_updates = data

        if cached:
            for token in self._replay_cached_tokens(saved_updates):
                yield token

    def _create_configurable(self, session_id: str) -> dict:
        return {"configurable": {"thread_id": session_id}}

    @staticmethod
    def _replay_cached_tokens(saved_updates: dict):
        """To imitate streaming from cached tokens with the
        same output format as the messages stream"""

        message = saved_updates["chatbot"]["messages"][0].content
        lines = message.splitlines(keepends=True)  # Preserve line breaks

        for line in lines:
            stripped = line.strip()
            if not stripped:
                yield "\n"
                continue

            words = stripped.split()
            yield words[0]
            for w in words[1:]:
                yield " " + w
            yield "\n"
