"""Application configuration from environment variables."""

import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Application settings loaded from environment."""

    # Firebase
    FB_PROJECT_ID: str = os.getenv("FB_PROJECT_ID", "")
    FB_PRIVATE_KEY: str = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
    FB_CLIENT_EMAIL: str = os.getenv("FB_CLIENT_EMAIL", "")

    # Slack
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_CHANNEL_ID: str = os.getenv("SLACK_CHANNEL_ID", "")

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5")
    OPENAI_API_VERSION: str = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")


settings = Settings()
