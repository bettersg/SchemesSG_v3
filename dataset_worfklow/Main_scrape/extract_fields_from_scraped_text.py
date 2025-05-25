import pandas as pd
import os
from dotenv import dotenv_values, load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.utils.function_calling import tool_example_to_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import TokenTextSplitter
from dataset_worfklow.constants import (
    WHAT_IT_GIVES,
    WHO_IS_IT_FOR,
    SCHEME_TYPE,
    SEARCH_BOOSTER,
)
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage


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

    address: Optional[str] = Field(
        default=None,
        description="Full Singapore address extracted from the scraped website text. Examples: '123 Orchard Road, #05-67, Singapore 238888', 'Blk 456 Ang Mo Kio Ave 10, #01-789, Singapore 560456'.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Singapore phone number extracted from the scraped website text. Examples: '+65 6123 4567', '61234567', '8765 4321'.",
    )
    email: Optional[str] = Field(
        default=None,
        description="Relevant email address extracted from the scraped website text. Example: 'contact_us@agency.gov.sg'.",
    )
    llm_description: Optional[str] = Field(
        default=None,
        description="Concise description of the scheme extracted from the scraped website text, summarizing key details for quick understanding. Aim for under 200 words.",
    )
    eligibility: Optional[str] = Field(
        default=None,
        description="Extract all eligibility criteria mentioned in the scraped text, including any specific requirements or necessary documents.",
    )
    how_to_apply: Optional[str] = Field(
        default=None,
        description="Extract the step-by-step application process described in the scraped text. Include details on where or how to apply.",
    )
    who_is_it_for: Optional[str] = Field(
        default=None,
        description=f"Who is this scheme for as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHO_IS_IT_FOR}",
    )
    what_it_gives: Optional[str] = Field(
        default=None,
        description=f"What does this scheme give as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {WHAT_IT_GIVES}",
    )
    scheme_type: Optional[str] = Field(
        default=None,
        description=f"What is this scheme type as explained in the scraped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {SCHEME_TYPE}",
    )
    search_booster: Optional[str] = Field(
        default=None,
        description=f"How would people search for this scheme, infer from scaped text? Must belong to one or many of this list, and separate by commas if there are multiple values: {SEARCH_BOOSTER}",
    )


class SchemesSummaryStructuredOutput(BaseModel):
    """Extract a one-sentence summary about the scheme based on the information provided."""
    summary: Optional[str] = Field(
        default=None,
        description="A single-sentence summary of the scheme, extracted from the provided information. Should concisely capture the essence of the scheme in one sentence.",
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
        self.no_valuable_text_examples = self._init_examples()
        self.max_tokens = 450000
        self.text_splitter = self._init_text_splitter()

    def reformat_llm_description(self, text):
        """Use the LLM to re-format the description"""
        if text is None:
            return None
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert formatter for UI and frontend websites."
                    "You are able to format text using '/n' in the best ways"
                ),
                ("human", "Format the following in the best way to render on UI:{text}"),
            ]
        )
        prompt = prompt_template.invoke({"text": text})
        messages = prompt.to_messages()
        return self.open_ai_client.invoke(messages).content

    def extract_text(self, text: str):
        structured_llm = self.open_ai_client.with_structured_output(
            SchemesStructuredOutput
        )
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert extraction algorithm. "
                    "Only extract relevant information from the text. "
                    "If you do not know the value of an attribute asked to extract, "
                    "return null for the attribute's value.",
                ),
                ("human", "{text}"),
            ]
        )
        if len(text) > self.max_tokens:
            # if length of text exceeds max tokens, split the text into chunks to run extraction over it
            texts = self.text_splitter.split_text(text)
            data_models = []
            for text in texts:
                prompt = prompt_template.invoke({"text": text})
                messages = prompt.to_messages()
                data_model = structured_llm.invoke(
                    self.no_valuable_text_examples + messages
                )
                data_models.append(data_model)
            # combine extraction results into one model
            data_model = self.merge_models_concat(data_models)
        else:
            prompt = prompt_template.invoke({"text": text})
            messages = prompt.to_messages()
            data_model = structured_llm.invoke(self.no_valuable_text_examples + messages)
        # format llm description into something that is more readable
        data_model.llm_description = self.reformat_llm_description(data_model.llm_description)
        return data_model

    def _init_examples(self):
        """Generate negative examples for the model to ignore"""
        messages = []
        examples = [
            (
                "You are being redirected...Javascript is required. Please enable javascript before you are allowed to see this page.",
                SchemesStructuredOutput(),
            ),
            (
                "SupportGoWhereYou need to enable JavaScript to run this app.",
                SchemesStructuredOutput(),
            ),
            (
                "ERROR: HTTP Error: 403.",
                SchemesStructuredOutput(),
            ),

        ]
        for txt, tool_call in examples:
            ai_response = "Detected no structured output."
            messages.extend(
                tool_example_to_messages(txt, [tool_call], ai_response=ai_response)
            )
        return messages

    def _init_text_splitter(self):
        """Intialize text splitter for splitting text across chunks"""
        text_splitter = TokenTextSplitter(
            # Controls the size of each chunk
            chunk_size=self.max_tokens,
            # Controls overlap between chunks
            chunk_overlap=20,
        )
        return text_splitter

    def merge_models_concat(
        self, instances: List[SchemesStructuredOutput]
    ) -> SchemesStructuredOutput:
        """Merge multiple instances of SchemesStructuredOutput to produce one instance of SchemesStructuredOutput"""
        merged_data = {field: "" for field in SchemesStructuredOutput.__fields__}
        for field in SchemesStructuredOutput.__fields__:
            parts = [
                getattr(instance, field)
                for instance in instances
                if getattr(instance, field) is not None
            ]
            merged_data[field] = ",".join(parts) if parts else None
        return SchemesStructuredOutput(**merged_data)

    def generate_summary(self, text):
        """Use the LLM to generate a one-sentence summary about the scheme."""
        if text is None:
            return None
        from .extract_fields_from_scraped_text import SchemesSummaryStructuredOutput
        structured_llm = self.open_ai_client.with_structured_output(SchemesSummaryStructuredOutput)
        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert at summarizing information. Generate a single, concise sentence that captures the essence of the scheme based on the provided text. Maximum 10 words.",
            ),
            ("human", "{text}"),
        ])
        prompt = prompt_template.invoke({"text": text})
        messages = prompt.to_messages()
        data_model = structured_llm.invoke(messages)
        return data_model.summary
