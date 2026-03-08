"""Configuration for LLM chatbot parameters"""

from dataclasses import dataclass


# LLM Configuration Constants
PROVIDER_MODEL_NAME = "azure_openai:gpt-5"
CHATBOT_MAX_COMPLETION_TOKENS = 4096


@dataclass
class ChatbotConfig:
    """Configuration for LLM chatbot parameters.

    GPT-5 is a reasoning model that does not support custom temperature,
    top_p, presence_penalty, or frequency_penalty. Temperature must be
    explicitly set to 1 (the only accepted value) to override langchain's
    default of 0.7. Uses max_completion_tokens instead of max_tokens.
    """

    temperature: float = 1.0
    max_completion_tokens: int = CHATBOT_MAX_COMPLETION_TOKENS
