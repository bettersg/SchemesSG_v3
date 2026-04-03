"""Runtime-specific configuration for main agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_MAIN_AGENT_MAX_COMPLETION_TOKENS = 4096


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class MainAgentRuntimeConfig:
    """Main-agent runtime config.

    Supports dedicated env vars so main agent can use different deployment/model
    from other runtimes (for example followup runtime).
    """

    azure_deployment: str = os.getenv(
        "MAIN_AGENT_AZURE_OPENAI_DEPLOYMENT_NAME",
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    )
    openai_api_version: str = os.getenv(
        "MAIN_AGENT_OPENAI_API_VERSION",
        os.getenv("OPENAI_API_VERSION", "2024-12-01-preview"),
    )
    temperature: float = 1.0
    max_completion_tokens: int = _get_env_int(
        "MAIN_AGENT_MAX_COMPLETION_TOKENS",
        DEFAULT_MAIN_AGENT_MAX_COMPLETION_TOKENS,
    )

    @property
    def provider_model_name(self) -> str:
        return f"azure_openai:{self.azure_deployment}"
