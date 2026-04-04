"""Runtime-specific configuration for followup agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_FOLLOWUP_MAX_COMPLETION_TOKENS = 400


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class FollowupRuntimeConfig:
    """Followup runtime config independent from main agent runtime."""

    azure_deployment: str = os.getenv(
        "FOLLOWUP_AZURE_OPENAI_DEPLOYMENT_NAME",
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )
    openai_api_version: str = os.getenv(
        "FOLLOWUP_OPENAI_API_VERSION",
        os.getenv("OPENAI_API_VERSION", "2024-12-01-preview"),
    )
    temperature: float = 1.0
    max_completion_tokens: int = _get_env_int(
        "FOLLOWUP_MAX_COMPLETION_TOKENS",
        DEFAULT_FOLLOWUP_MAX_COMPLETION_TOKENS,
    )

    @property
    def provider_model_name(self) -> str:
        return f"azure_openai:{self.azure_deployment}"
