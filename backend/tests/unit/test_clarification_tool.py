"""Unit tests for the explicit clarification tool."""

import importlib.util
from pathlib import Path


CLARIFICATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "functions"
    / "agent"
    / "tools"
    / "clarification.py"
)
spec = importlib.util.spec_from_file_location("clarification", CLARIFICATION_PATH)
clarification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clarification)


def test_request_clarification_returns_structured_questions():
    result = clarification.request_clarification(
        "User only asked for help.",
        [
            "What kind of support do you need most urgently?",
            "Who is the support for?",
        ],
    )

    assert result["needs_clarification"] is True
    assert result["reason"] == "User only asked for help."
    assert result["questions"] == [
        "What kind of support do you need most urgently?",
        "Who is the support for?",
    ]
    assert "Do not search schemes" in result["instruction"]


def test_request_clarification_keeps_at_most_two_nonempty_questions():
    result = clarification.request_clarification(
        "Too broad.",
        [
            "What support do you need?",
            "",
            "Who is it for?",
            "How urgent is it?",
        ],
    )

    assert result["questions"] == [
        "What support do you need?",
        "Who is it for?",
    ]
