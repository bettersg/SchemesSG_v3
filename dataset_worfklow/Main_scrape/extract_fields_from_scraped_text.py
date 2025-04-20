import pandas as pd
import os
from dotenv import dotenv_values, load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dataset_worfklow.constants import WHAT_IT_GIVES, WHO_IS_IT_FOR, SCHEME_TYPE, SEARCH_BOOSTER

class Config:
    def __init__(self):
        load_dotenv("backend/functions/.env")

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr


class SchemesStructuredOutput(BaseModel):
    """Extract information from the description of the scheme."""
    llm_address: Optional[str] = Field(
        default=None, description="Location in the description"
    )
    llm_phone: Optional[str] = Field(
        default=None, description="Phone number in the description"
    )
    llm_email: Optional[str] = Field(
        default=None, description="Relevant email in the description"
    )
    llm_description: Optional[str] = Field(
        default=None, description="Concise description of the scheme"
    )
    llm_eligibility: Optional[str] = Field(
        default=None, description="Eligibility criteria and documents needed for scheme in the description"
    )
    llm_how_to_apply: Optional[str] = Field(
        default=None, description="Application process of the scheme in the description"
    )
    llm_who_is_it_for: Optional[str] = Field(default=None, description=f"Who is this scheme for? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHO_IS_IT_FOR}")
    llm_what_it_gives: Optional[str] = Field(default=None, description=f"What does this scheme give? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHAT_IT_GIVES}")
    llm_scheme_type: Optional[str] =  Field(default=None, description=f"What does this scheme type belong to? Must belong to one or many of this list, and separate by commas if there are multiple values: {SCHEME_TYPE}")
    llm_search_booster: Optional[str]  =  Field(default=None, description=f"Adds some search booster? Must belong to one or many of this list, and separate by commas if there are multiple values: {SCHEME_TYPE}")

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
