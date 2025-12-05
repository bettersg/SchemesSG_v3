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
from loguru import logger
from datetime import datetime
from logging_config import ensure_logging_setup
from src.constants import (
    WHAT_IT_GIVES,
    WHO_IS_IT_FOR,
    SCHEME_TYPE,
    SEARCH_BOOSTER,
)

from langchain_core.messages import HumanMessage, SystemMessage

class Config:
    def __init__(self):
        # Get the path to the .env file relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, "..", "..", ".env")
        load_dotenv(env_path)

        # Load all environment variables from .env file
        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        # Direct environment variable lookup using standard Azure OpenAI names
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr

class TokenCostTracker:
    """Utility class for tracking token usage and costs for Azure OpenAI models."""

    # Azure OpenAI pricing per 1000 tokens (as of 2024)
    # These are approximate rates - actual rates may vary
    PRICING = {
        "gpt-4.1": {
            "input": 0.40,  # $0.40 per 1000 input tokens
            "output": 1.60  # $1.60 per 1000 output tokens
        },
        "gpt-4.1-mini": {
            "input": 0.30,  # $0.30 per 1000 input tokens
            "output": 1.20  # $1.20 per 1000 output tokens
        },
        "gpt-5": {
            "input": 0.50,  # $0.50 per 1000 input tokens
            "output": 2.00  # $2.00 per 1000 output tokens
        },
        "gpt-5-nano": {
            "input": 0.40,  # $0.40 per 1000 input tokens
            "output": 1.60  # $1.60 per 1000 output tokens
        },
        # Legacy models for backward compatibility
        "gpt-4": {
            "input": 0.03,  # $0.03 per 1000 input tokens
            "output": 0.06  # $0.06 per 1000 output tokens
        },
        "gpt-4-32k": {
            "input": 0.06,  # $0.06 per 1000 input tokens
            "output": 0.12  # $0.12 per 1000 output tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.0015,  # $0.0015 per 1000 input tokens
            "output": 0.002  # $0.002 per 1000 output tokens
        }
    }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation of token count based on text length.
        This is an approximation - actual tokenization may vary."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return max(1, len(text) // 4)

    @staticmethod
    def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost based on token usage and model pricing."""
        if model_name not in TokenCostTracker.PRICING:
            # Default to GPT-4.1-mini pricing if model not found
            model_name = "gpt-4.1-mini"

        pricing = TokenCostTracker.PRICING[model_name]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    @staticmethod
    def log_llm_usage(operation: str, model_name: str, input_text: str, output_text: str = None):
        """Log token usage and cost for an LLM operation."""
        input_tokens = TokenCostTracker.estimate_tokens(input_text)
        output_tokens = TokenCostTracker.estimate_tokens(output_text) if output_text else 0
        total_tokens = input_tokens + output_tokens
        cost = TokenCostTracker.calculate_cost(model_name, input_tokens, output_tokens)

        logger.info(
            f"LLM Usage - {operation} | "
            f"Model: {model_name} | "
            f"Input tokens: {input_tokens} | "
            f"Output tokens: {output_tokens} | "
            f"Total tokens: {total_tokens} | "
            f"Estimated cost: ${cost:.6f}"
        )

        return {
            "operation": operation,
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        }

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
        description="Concise description of the scheme extracted from the scraped website text, summarizing key details for quick understanding. Aim for under 200 words. Use simple markdown formatting. For line breaks, use standard newline characters (\\n) naturally without any escape sequences or special symbols.",
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
            deployment_name=config.azure_openai_chat_deployment,
            azure_endpoint=config.azure_openai_endpoint,
            openai_api_version=config.openai_api_version,
            openai_api_key=config.azure_openai_api_key,
            openai_api_type=config.azure_openai_type,
            model_name=config.azure_openai_chat_deployment,
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

    def clean_llm_description_text(self, text: str) -> str:
        """Clean llm_description text by removing forward slash n symbols and other formatting issues."""
        if not text:
            return text

        # Remove forward slash n patterns: /n, \n, \/n etc.
        import re

        # Replace various forward slash n patterns with proper newlines
        text = re.sub(r'/n', '\n', text)  # Replace /n with \n
        text = re.sub(r'\\/n', '\n', text)  # Replace \/n with \n
        text = re.sub(r'\\n', '\n', text)  # Replace \\n with \n

        # Remove carriage return symbols and other invisible characters
        text = text.replace('\r', '').replace('\t', ' ')

        # Clean up multiple consecutive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Clean up extra whitespace
        text = re.sub(r'[ ]+', ' ', text)  # Multiple spaces to single space
        text = text.strip()

        return text

    def reformat_llm_description(self, text):
        """Use the LLM to re-format the description"""
        if text is None:
            return None

        # First clean the text using our cleaning function
        text = self.clean_llm_description_text(text)

        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert formatter for UI and frontend websites. "
                "You format text for clear readability using proper newline characters. "
                "Use standard newline characters (\\n) naturally for line breaks. "
                "Do not use forward slashes with n (/n) or any escape sequences. "
                "Focus on clean, readable formatting suitable for web display."
            ),
            ("human", "Format the following text for optimal UI display:\n\n{text}"),
        ])

        prompt = prompt_template.invoke({"text": text})
        messages = prompt.to_messages()

        # Log token usage and cost before making the call
        input_text = str(messages)
        TokenCostTracker.log_llm_usage(
            operation="reformat_llm_description",
            model_name=self.open_ai_client.model_name,
            input_text=input_text
        )

        response = self.open_ai_client.invoke(messages)

        # Log the output tokens and cost after getting the response
        output_text = response.content
        TokenCostTracker.log_llm_usage(
            operation="reformat_llm_description_output",
            model_name=self.open_ai_client.model_name,
            input_text="",  # No input for output logging
            output_text=output_text
        )

        # Clean the response again to ensure no formatting issues remain
        cleaned_output = self.clean_llm_description_text(output_text)

        return cleaned_output

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

        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert extraction algorithm. "
                "Your goal is to extract the requested attributes as accurately and faithfully as possible "
                "from the given website text. "
                "Use wording, definitions, and phrases that stay close to the original text so the extracted "
                "results can be trusted as reflecting the website accurately. "
                "At the same time, ensure compliance with copyright and content rules: "
                "reproduce only short, necessary snippets or factual values, not large verbatim portions of text. "
                "If the value of an attribute cannot be confidently determined, return null. "
                "For physical locations, be careful to distinguish between multiple distinct locations versus "
                "multiple contact methods at a single location. "
                "For text formatting, use natural newline characters without escape sequences or special symbols. "
                "Do not infer, hallucinate, or summarize beyond what is explicitly written in the provided text."
            ),
            ("human", "{text}"),
        ])

        if len(text) > self.max_tokens:
            # if length of text exceeds max tokens, split the text into chunks to run extraction over it
            texts = self.text_splitter.split_text(text)
            data_models = []
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0

            for i, text_chunk in enumerate(texts):
                prompt = prompt_template.invoke({"text": text_chunk})
                messages = prompt.to_messages()
                full_messages = self.no_valuable_text_examples + messages

                # Log token usage for each chunk
                input_text = str(full_messages)
                usage_info = TokenCostTracker.log_llm_usage(
                    operation=f"extract_text_chunk_{i+1}",
                    model_name=self.open_ai_client.model_name,
                    input_text=input_text
                )
                total_input_tokens += usage_info["input_tokens"]

                data_model = structured_llm.invoke(full_messages)
                data_models.append(data_model)

                # Log output tokens for this chunk
                output_text = str(data_model.dict())
                output_usage_info = TokenCostTracker.log_llm_usage(
                    operation=f"extract_text_chunk_{i+1}_output",
                    model_name=self.open_ai_client.model_name,
                    input_text="",
                    output_text=output_text
                )
                total_output_tokens += output_usage_info["output_tokens"]
                total_cost += output_usage_info["cost"]

            # Log total usage for chunked processing
            logger.info(
                f"LLM Usage - extract_text_chunked_total | "
                f"Model: {self.open_ai_client.model_name} | "
                f"Total input tokens: {total_input_tokens} | "
                f"Total output tokens: {total_output_tokens} | "
                f"Total tokens: {total_input_tokens + total_output_tokens} | "
                f"Total estimated cost: ${total_cost:.6f} | "
                f"Chunks processed: {len(texts)}"
            )

            # combine extraction results into one model
            data_model = self.merge_models_concat(data_models)
        else:
            prompt = prompt_template.invoke({"text": text})
            messages = prompt.to_messages()
            full_messages = self.no_valuable_text_examples + messages

            # Log token usage for single text processing
            input_text = str(full_messages)
            TokenCostTracker.log_llm_usage(
                operation="extract_text_single",
                model_name=self.open_ai_client.model_name,
                input_text=input_text
            )

            data_model = structured_llm.invoke(full_messages)

            # Log output tokens
            output_text = str(data_model.dict())
            TokenCostTracker.log_llm_usage(
                operation="extract_text_single_output",
                model_name=self.open_ai_client.model_name,
                input_text="",
                output_text=output_text
            )

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
