"""Tool for explicit clarification turns before running scheme search."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


MAX_QUESTIONS = 2


class RequestClarificationInput(BaseModel):
    reason: str = Field(
        ...,
        min_length=1,
        description="Brief reason the current user request is too vague for a useful schemes search.",
    )
    questions: list[str] = Field(
        ...,
        min_length=1,
        max_length=MAX_QUESTIONS,
        description="One or two concise questions that would make the scheme search specific enough.",
    )


def request_clarification(reason: str, questions: list[str]) -> dict[str, Any]:
    """Return a structured clarification request instead of searching."""

    clean_questions = [question.strip() for question in questions if question.strip()][:MAX_QUESTIONS]
    return {
        "needs_clarification": True,
        "reason": reason.strip(),
        "questions": clean_questions,
        "instruction": "Ask these clarification questions to the user. Do not search schemes until the user answers.",
    }


request_clarification_tool = StructuredTool.from_function(
    func=request_clarification,
    name="request_clarification",
    description=(
        "Use this when the user's scheme-search intent is too vague to run a meaningful database search. "
        "It returns the clarification questions the assistant should ask before searching."
    ),
    args_schema=RequestClarificationInput,
)


__all__ = ["request_clarification_tool"]
