"""
Load Azure OpenAI LLMs dynamically by deployment name.

This module validates model config, initializes the selected Azure LLM,
and makes it easy to add new deployed models in the future.
"""

import os
from dataclasses import dataclass
from typing import Dict

from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()

PRESET_LLM_CONFIGS = {
    "gpt-5.4": {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_EASTUS2"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_EASTUS2"),
        "api_version": os.getenv("OPENAI_API_VERSION"),
    },
    "gpt-5.4-mini": {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_SEA"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_SEA"),
        "api_version": os.getenv("OPENAI_API_VERSION"),
    },
    "gpt-4.1-mini": {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_JAPANEAST"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_JAPANEAST"),
        "api_version": os.getenv("OPENAI_API_VERSION"),
    },
}


@dataclass(frozen=True)
class LLMConfig:
    """Minimal, validated config needed to initialize an Azure OpenAI client.

    `deployment_name` is also the key used in `PRESET_LLM_CONFIGS`.
    """

    endpoint: str
    api_key: str
    api_version: str
    deployment_name: str

    @classmethod
    def from_preset(
        cls,
        deployment_name: str,
        preset_configs: Dict[str, Dict[str, str]] | None = None,
    ) -> "LLMConfig":
        """Load and validate config from preset dictionary by deployment name."""
        presets = preset_configs or PRESET_LLM_CONFIGS
        if deployment_name not in presets:
            raise ValueError(f"Invalid deployment_name '{deployment_name}': no preset found")

        cfg = presets[deployment_name]
        endpoint = cfg.get("endpoint")
        api_key = cfg.get("api_key")
        api_version = cfg.get("api_version") or os.getenv("OPENAI_API_VERSION", "2024-12-01-preview")

        if not endpoint or not api_key:
            raise ValueError(f"Invalid deployment_name '{deployment_name}': preset is missing endpoint/api_key")

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
        )


class LLMManager:
    """Manager that loads configs from presets and initializes Azure OpenAI LLMs.

    Preferred usage:
    - `LLMManager(deployment_name="gpt-5.4")` for one-step load from presets.
    - Or pass an explicit validated `LLMConfig` object.
    """

    def __init__(
        self,
        deployment_name: str | None = None,
        llm_config: LLMConfig | None = None,
        preset_configs: Dict[str, Dict[str, str]] | None = None,
    ):
        if llm_config is None:
            if not deployment_name:
                raise ValueError("Either llm_config or deployment_name must be provided")
            llm_config = LLMConfig.from_preset(deployment_name, preset_configs)

        self.config = llm_config
        self.model = self._initialize_model(self.config)

    @staticmethod
    def _initialize_model(config: LLMConfig) -> AzureChatOpenAI:
        return AzureChatOpenAI(
            api_version=config.api_version,
            azure_endpoint=config.endpoint,
            api_key=config.api_key,
            model_name=config.deployment_name,
        )

    def get_llm(self) -> AzureChatOpenAI:
        """Return the initialized LLM instance."""
        return self.model

    def modify_llm(self, **kwargs) -> None:
        """Modify attributes of the underlying LLM instance."""
        for key, value in kwargs.items():
            setattr(self.model, key, value)
