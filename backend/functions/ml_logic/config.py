"""Configuration for LLM chatbot parameters"""

from dataclasses import dataclass


# LLM Configuration Constants
PROVIDER_MODEL_NAME = "azure_openai:gpt-5"
CHATBOT_MAX_COMPLETION_TOKENS = 512


@dataclass
class ChatbotConfig:
    """Configuration for LLM chatbot parameters.

    GPT-5 is a reasoning model that does not support temperature, top_p,
    presence_penalty, or frequency_penalty. Uses max_completion_tokens
    instead of max_tokens.
    """

    max_completion_tokens: int = CHATBOT_MAX_COMPLETION_TOKENS
