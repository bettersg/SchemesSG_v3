"""Configuration for LLM chatbot parameters"""

from dataclasses import dataclass

# LLM Configuration Constants
PROVIDER_MODEL_NAME = "azure_openai:gpt-4.1-mini"
CHATBOT_TEMPERATURE = 0.1
CHATBOT_TOP_P = 0.9
CHATBOT_PRESENCE_PENALTY = 0.2
CHATBOT_FREQUENCY_PENALTY = 0.2
CHATBOT_MAX_TOKENS = 512


@dataclass
class ChatbotConfig:
    """Configuration for LLM chatbot parameters"""

    temperature: float = CHATBOT_TEMPERATURE
    top_p: float = CHATBOT_TOP_P
    presence_penalty: float = CHATBOT_PRESENCE_PENALTY
    frequency_penalty: float = CHATBOT_FREQUENCY_PENALTY
    max_tokens: int = CHATBOT_MAX_TOKENS
