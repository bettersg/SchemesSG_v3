"""Tool that returns reusable response skills for the main agent."""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


CLARIFICATION_QUESTIONS_PROMPT = (
    "Ask at most 2 brief clarification questions only when the user request is too vague "
    "to run a meaningful schemes search. Prioritize questions that unblock eligibility "
    "matching: household profile, target need, and urgency/timeframe. If existing context "
    "already makes intent clear, do not ask clarifications and proceed with search immediately."
)

SUMMARY_SUCCINCT_ANSWER_PROMPT = (
    "Keep final user-facing answers under 50 words. Use concise, mobile-friendly phrasing, "
    "avoid repeating full scheme card details, and include only the most actionable next step(s)."
)

DRAFT_EMAIL_PROMPT = (
    "Draft emails with a useful subject line when appropriate, a polite greeting, concise context, "
    "a specific ask, and a courteous close. Use placeholders such as [Your name] or [Phone number] "
    "for unknown personal details instead of inventing them. Match the user's requested language, "
    "or the user's language if no language is requested. Keep proper nouns, scheme names, agency "
    "names, URLs, emails, and phone numbers exactly as given. Do not emit stray, decorative, or "
    "out-of-place characters from unrelated writing systems, including stray Tamil characters in "
    "an English email."
)


class LoadSkillsInput(BaseModel):
    skill: Literal["all", "clarification_questions", "summary_succinct_answer", "draft_email"] = Field(
        default="all",
        description=(
            "Skill bundle to load. Use 'clarification_questions' for question strategy, "
            "'summary_succinct_answer' for compact response style, 'draft_email' for "
            "email drafting rules, or 'all' for every skill."
        ),
    )


def _build_skills_payload(skill: str) -> dict[str, Any]:
    skills = {
        "clarification_questions": CLARIFICATION_QUESTIONS_PROMPT,
        "summary_succinct_answer": SUMMARY_SUCCINCT_ANSWER_PROMPT,
        "draft_email": DRAFT_EMAIL_PROMPT,
    }

    if skill == "clarification_questions":
        selected = {"clarification_questions": skills["clarification_questions"]}
    elif skill == "summary_succinct_answer":
        selected = {"summary_succinct_answer": skills["summary_succinct_answer"]}
    elif skill == "draft_email":
        selected = {"draft_email": skills["draft_email"]}
    else:
        selected = skills

    return {
        "skill": skill,
        "skills": selected,
        "note": "Use these directives to shape tool routing and response style.",
    }


def _load_skills_sync(
    skill: Literal["all", "clarification_questions", "summary_succinct_answer", "draft_email"] = "all",
) -> dict[str, Any]:
    return _build_skills_payload(skill)


async def _load_skills_async(
    skill: Literal["all", "clarification_questions", "summary_succinct_answer", "draft_email"] = "all",
) -> dict[str, Any]:
    return await asyncio.to_thread(_build_skills_payload, skill)


load_skills_tool = StructuredTool.from_function(
    func=_load_skills_sync,
    coroutine=_load_skills_async,
    name="load_skills",
    description=(
        "Load optional response skills that improve behavior quality, including clarification-question "
        "strategy, concise mobile-friendly summary style, and email drafting rules."
    ),
    args_schema=LoadSkillsInput,
)


__all__ = ["load_skills_tool"]
