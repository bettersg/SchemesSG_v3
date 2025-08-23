import pandas as pd
import os
from dotenv import dotenv_values, load_dotenv
from langchain_openai import AzureChatOpenAI
from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from langchain_core.utils.function_calling import tool_example_to_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_text_splitters import TokenTextSplitter
from langchain_core.caches import InMemoryCache
import hashlib
from constants import (
    WHAT_IT_GIVES,
    WHO_IS_IT_FOR,
    SCHEME_TYPE,
    SEARCH_BOOSTER,
)
from langchain_core.messages import HumanMessage, SystemMessage


class Config:
    def __init__(self):
        load_dotenv("dataset_workflow/.env")

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr


class PhysicalLocation(BaseModel):
    """Represents a physical location with its contact information."""

    location_name: Optional[str] = Field(
        default=None,
        description="Name or identifier for this location (e.g., 'Main Office', 'Branch Office', 'Service Center'). If no specific name is given, use a descriptive name based on the address or context.",
    )
    address: Optional[str] = Field(
        default=None,
        description="Full Singapore address for this location. Examples: '123 Orchard Road, #05-67, Singapore 238888', 'Blk 456 Ang Mo Kio Ave 10, #01-789, Singapore 560456'.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Phone number for this specific location. Examples: '+65 6123 4567', '61234567', '8765 4321'. If multiple phones for same location, separate with commas.",
    )
    email: Optional[str] = Field(
        default=None,
        description="Email address for this specific location. Example: 'contact_us@agency.gov.sg'. If multiple emails for same location, separate with commas.",
    )


class SchemesStructuredOutput(BaseModel):
    """Extract information from the description of the scheme."""

    physical_locations: Optional[List[PhysicalLocation]] = Field(
        default=None,
        description="List of physical locations with their contact information. For single location schemes, create one location object. For multiple locations, create separate objects for each location. Each location should have its associated phone and email.",
    )
    llm_description: Optional[str] = Field(
        default=None,
        description="Concise description of the scheme extracted from the scraped website text, summarizing key details for quick understanding. Aim for under 200 words. Use simple markdown. Do not use forward slash n (/n) to indicate next line. Only use back slash n.",
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
    service_area: Optional[str] = Field(
        default=None,
        description="Service area boundaries for this scheme. If the scheme has specific service boundaries (e.g., only residents of certain towns can apply), list the town names separated by commas (e.g., 'Toa Payoh, Novena, Marsiling'). If there are no service boundaries and the scheme is available to all Singapore residents, return 'No Service Boundaries'.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="A single-sentence summary of the scheme, extracted from the scraped text. Should concisely capture the essence of the scheme in one sentence. Maximum 10 words.",
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
            deployment_name=config.deployment41,
            azure_endpoint=config.endpoint,
            openai_api_version=config.version,
            openai_api_key=config.apikey,
            openai_api_type=config.type,
            model_name=config.model41,
            temperature=0,
        )

    def _initialize_app(self):
        self.open_ai_client = self.init_chatbot()
        self.no_valuable_text_examples = self._init_examples()
        self.max_tokens = 450000
        self.text_splitter = self._init_text_splitter()
        # Initialize cache for structured output extraction
        self.cache = InMemoryCache(maxsize=2000)  # Cache up to 2000 extractions
        self.llm_string = "azure_openai_text_extract"

    def _generate_cache_key(self, text: str) -> str:
        """Generate a hashed cache key from the input text."""
        return hashlib.sha256(text.encode()).hexdigest()

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

    def transform_to_database_format(self, data_model: SchemesStructuredOutput):
        """Transform the structured output to database format based on the 3 scenarios"""
        if not data_model.physical_locations:
            return {
                'address': None,
                'phone': None,
                'email': None
            }

        locations = data_model.physical_locations

        # Scenario 1: Single location
        if len(locations) == 1:
            location = locations[0]
            return {
                'address': location.address,
                'phone': location.phone,
                'email': location.email
            }

        # Scenario 2: Single location but multiple phones/emails
        elif len(locations) == 1 and (',' in locations[0].phone or ',' in locations[0].email):
            location = locations[0]
            return {
                'address': location.address,
                'phone': location.phone,
                'email': location.email
            }

        # Scenario 3: Multiple physical locations
        else:
            addresses = [loc.address for loc in locations if loc.address]
            phones = [loc.phone for loc in locations if loc.phone]
            emails = [loc.email for loc in locations if loc.email]

            return {
                'address': addresses if len(addresses) > 1 else (addresses[0] if addresses else None),
                'phone': phones if len(phones) > 1 else (phones[0] if phones else None),
                'email': emails if len(emails) > 1 else (emails[0] if emails else None)
            }

    def extract_text(self, text: str):
        # Check cache first
        cache_key = self._generate_cache_key(text)
        cached_response = self.cache.lookup(self.llm_string, cache_key)
        if cached_response:
            print(f"Cache hit for text extraction (key: {cache_key[:8]}...)")
            return cached_response

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
                    "return null for the attribute's value. "
                    "For physical locations, carefully identify if there are multiple distinct locations "
                    "or if there are multiple contact methods for the same location.",
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

        # Cache the result
        self.cache.update(self.llm_string, cache_key, data_model)
        print(f"Cached text extraction result (key: {cache_key[:8]}...)")

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
            tool_output = "Detected no structured output."
            messages.extend(
                tool_example_to_messages(txt, [tool_call], tool_outputs=[tool_output])
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

        # Special handling for physical_locations - combine all locations
        all_locations = []
        for instance in instances:
            if instance.physical_locations:
                all_locations.extend(instance.physical_locations)
        merged_data['physical_locations'] = all_locations if all_locations else None

        # Handle other fields
        for field in SchemesStructuredOutput.__fields__:
            if field == 'physical_locations':
                continue  # Already handled above
            parts = [
                getattr(instance, field)
                for instance in instances
                if getattr(instance, field) is not None
            ]
            merged_data[field] = ",".join(parts) if parts else None
        return SchemesStructuredOutput(**merged_data)
