"""Canonical event type definitions for agent streaming."""

from __future__ import annotations

from enum import Enum


class _StringEnum(str, Enum):
    """Python 3.10-compatible string enum base."""


class AgentStreamEventType(_StringEnum):
    STATUS = "status"
    CHUNK = "chunk"
    SCHEMES_UPDATE = "schemes_update"
    ASSISTANT = "assistant"
    STATE = "state"
    FOLLOWUPS = "followups"
    DONE = "done"


__all__ = ["AgentStreamEventType"]
