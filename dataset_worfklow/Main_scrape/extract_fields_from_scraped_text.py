import pandas as pd
import os
from dotenv import dotenv_values, load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dataset_worfklow.constants import WHAT_IT_GIVES, WHO_IS_IT_FOR, SCHEME_TYPE, SEARCH_BOOSTER

class Config:
    def __init__(self):
        load_dotenv(".env")

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
        default=None, description="Full Singapore address extracted from the scraped website text. Examples: '123 Orchard Road, #05-67, Singapore 238888', 'Blk 456 Ang Mo Kio Ave 10, #01-789, Singapore 560456'."
    )
    phone: Optional[str] = Field(
        default=None, description="Singapore phone number extracted from the scraped website text. Examples: '+65 6123 4567', '61234567', '8765 4321'."
    )
    email: Optional[str] = Field(
        default=None, description="Relevant email address extracted from the scraped website text. Example: 'contact_us@agency.gov.sg'."
    )
    llm_description: Optional[str] = Field(
        default=None, description="Concise description of the scheme extracted from the scraped website text, summarizing key details for quick understanding. Aim for under 200 words."
    )
    eligibility: Optional[str] = Field(
        default=None, description="Extract all eligibility criteria mentioned in the scraped text, including any specific requirements or necessary documents."
    )
    how_to_apply: Optional[str] = Field(
        default=None, description="Extract the step-by-step application process described in the scraped text. Include details on where or how to apply."
    )
    who_is_it_for: Optional[str] = Field(default=None, description=f"Who is this scheme for as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHO_IS_IT_FOR}")
    what_it_gives: Optional[str] = Field(default=None, description=f"What does this scheme give as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHAT_IT_GIVES}")
    scheme_type: Optional[str] =  Field(default=None, description=f"What is this scheme type as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {SCHEME_TYPE}")
    search_booster: Optional[str]  =  Field(default=None, description=f"How would people search for this scheme, infer from scaped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {SEARCH_BOOSTER}")

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
        # Truncate text to fit within model context limits, leaving room for output
        max_chars = 450000
        truncated_text = text[:max_chars]

        structured_llm = self.open_ai_client.with_structured_output(
            SchemesStructuredOutput
        )
        return structured_llm.invoke(truncated_text)
