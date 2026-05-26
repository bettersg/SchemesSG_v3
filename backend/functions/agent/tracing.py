from langfuse import get_client
from langfuse.langchain import CallbackHandler
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def load_langfuse_client_and_handler():
    """Initializes and returns a Langfuse client using environment variables."""
    client = get_client()

    if client.auth_check():
        logging.info("Langfuse client is authenticated and ready!")
    else:
        logging.error("Langfuse authentication failed. Please check your credentials and host.")
    handler = CallbackHandler()
    return client, handler
