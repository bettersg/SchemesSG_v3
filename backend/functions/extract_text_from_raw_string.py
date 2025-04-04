import pandas as pd
import os
from dotenv import dotenv_values, load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import Optional
from pydantic import BaseModel, Field


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


class SchemesStructuredOutput(BaseModel):
    """Extract information from the description of the scheme."""

    address: Optional[str] = Field(
        default=None, description="Location in the description"
    )
    phone: Optional[str] = Field(
        default=None, description="Phone number in the description"
    )
    email: Optional[str] = Field(
        default=None, description="Relevant email in the description"
    )
    purpose_of_scheme: Optional[str] = Field(
        default=None, description="Purpose of the scheme in the description"
    )
    website: Optional[str] = Field(
        default=None, description="Website in the description"
    )


class TextExtract:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TextExtract, cls).__new__(cls)
            cls._instance._initialize_app()

        return cls._instance

    def init_chatbot(self):
        config = Config()
        return AzureChatOpenAI(
            deployment_name=config.deployment,
            azure_endpoint=config.endpoint,
            openai_api_version=config.version,
            openai_api_key=config.apikey,
            openai_api_type=config.type,
            model_name=config.model,
            temperature=0,
        )

    def _initialize_app(self):
        self.open_ai_client = self.init_chatbot()

    def extract_text(self, text: str):
        structured_llm = self.open_ai_client.with_structured_output(
            SchemesStructuredOutput
        )
        return structured_llm.invoke(text)


df = pd.read_csv("../ml_logic/schemes-updated-with-text.csv")
text_extract = TextExtract()
for index, row in df.iterrows():
    print(row["Scraped Text"])
    print(text_extract.extract_text(row["Scraped Text"]))
    breakpoint()
