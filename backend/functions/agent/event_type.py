"""Canonical event type definitions for agent streaming."""

from __future__ import annotations

from enum import Enum


class _StringEnum(str, Enum):
    """Python 3.10-compatible string enum base."""


class AgentStreamEventType(_StringEnum):
    STATUS = "status"
    ACTION_MESSAGE = "action_message"
    TEXT = "text"
    SCHEMES_UPDATE = "schemes_update"
    SCHEMES = "schemes"
    FOLLOWUPS = "followups"
    DONE = "done"


class StatusPhase(_StringEnum):
    MESSAGE_START = "message_start"
    TOOL_COMPLETED = "tool_completed"
    SESSION_STARTED = "session_started"
    STARTED = "started"


__all__ = ["AgentStreamEventType", "StatusPhase"]
