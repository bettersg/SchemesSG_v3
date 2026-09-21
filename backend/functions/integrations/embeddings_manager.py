"""
Load Azure OpenAI embeddings dynamically by deployment name.

This module validates embedding config, initializes the selected Azure
embedding client, and keeps Azure wiring out of retrieval code.
"""

import os
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings

load_dotenv()


PRESET_EMBEDDING_CONFIGS = {
    "text-embedding-3-large": {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_SEA"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
        "api_version": os.getenv("OPENAI_API_VERSION"),
        "dimensions": 2048,
    }
}


@dataclass(frozen=True)
class EmbeddingsConfig:
    """Minimal, validated config needed to initialize Azure OpenAI embeddings."""

    endpoint: str
    api_key: str
    api_version: str
    deployment_name: str
    dimensions: int = 2048

    @classmethod
    def from_preset(
        cls,
        deployment_name: str,
        preset_configs: Dict[str, Dict[str, str]] | None = None,
    ) -> "EmbeddingsConfig":
        """Load and validate config from preset dictionary by deployment name."""
        presets = preset_configs or PRESET_EMBEDDING_CONFIGS
        if deployment_name not in presets:
            raise ValueError(f"Invalid deployment_name '{deployment_name}': no preset found")

        cfg = presets[deployment_name]
        endpoint = cfg.get("endpoint")
        api_key = cfg.get("api_key")
        api_version = cfg.get("api_version") or os.getenv("OPENAI_EMBEDDING_API_VERSION", "2024-12-01-preview")
        dimensions = int(cfg.get("dimensions", 2048))

        if not endpoint or not api_key:
            raise ValueError(f"Invalid deployment_name '{deployment_name}': preset is missing endpoint/api_key")

        return cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment_name,
            dimensions=dimensions,
        )


class EmbeddingsManager:
    """Manager that loads embedding configs from presets and initializes Azure embeddings."""

    def __init__(
        self,
        deployment_name: str | None = None,
        embedding_config: EmbeddingsConfig | None = None,
        preset_configs: Dict[str, Dict[str, str]] | None = None,
    ):
        if embedding_config is None:
            if not deployment_name:
                raise ValueError("Either embedding_config or deployment_name must be provided")
            embedding_config = EmbeddingsConfig.from_preset(deployment_name, preset_configs)

        self.config = embedding_config
        self.model = self._initialize_model(self.config)

    @staticmethod
    def _initialize_model(config: EmbeddingsConfig) -> AzureOpenAIEmbeddings:
        return AzureOpenAIEmbeddings(
            azure_endpoint=config.endpoint,
            api_key=config.api_key,
            api_version=config.api_version,
            model=config.deployment_name,
            dimensions=config.dimensions,
        )
