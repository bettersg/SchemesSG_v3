"""Scheme-processor LLM extraction: empty/cut-off replies must retry with a larger budget and never pass silently."""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


PROCESSOR_ROOT = Path(__file__).resolve().parents[2] / "scheme-processor"

PAGE = "Active Ageing Centres serve seniors with outreach and activities. " * 5
GOOD_JSON = json.dumps(
    {
        "llm_description": "Social activities for seniors",
        "summary": "Active ageing centres for seniors",
        "eligibility": "Seniors",
        "how_to_apply": "Walk in",
        "agency": "Fei Yue",
        "who_is_it_for": ["Seniors"],
        "what_it_gives": [],
        "scheme_type": [],
    }
)


def reply(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=finish_reason)],
        usage="usage",
    )


@pytest.fixture
def llm(monkeypatch):
    """Load llm_extractor against a fake litellm; replies are consumed in order and max_tokens recorded."""
    calls = []
    replies = []

    def completion(**kwargs):
        calls.append(kwargs)
        return replies.pop(0)

    fake = types.ModuleType("litellm")
    fake.completion = completion
    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.syspath_prepend(str(PROCESSOR_ROOT))
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.invalid")
    for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
        monkeypatch.delitem(sys.modules, name)
    module = importlib.import_module("app.services.llm_extractor")

    async def no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    return SimpleNamespace(module=module, calls=calls, replies=replies)


def run_extract(llm):
    return asyncio.run(llm.module.extract_with_llm(PAGE))


def test_first_budget_leaves_room_beyond_the_3000_tokens_that_reasoning_consumed_on_prod(llm):
    llm.replies.append(reply(GOOD_JSON))

    run_extract(llm)

    assert llm.calls[0]["max_completion_tokens"] > 3000


def test_empty_reply_retries_with_a_larger_budget_and_returns_the_fields(llm):
    llm.replies.extend([reply("", finish_reason="length"), reply(GOOD_JSON)])

    fields = run_extract(llm)

    assert fields["summary"] == "Active ageing centres for seniors"
    assert [c["max_completion_tokens"] for c in llm.calls] == list(llm.module.LLM_MAX_TOKENS)
    assert llm.calls[1]["max_completion_tokens"] > llm.calls[0]["max_completion_tokens"]


def test_reply_cut_off_at_the_cap_retries_instead_of_parsing_truncated_json(llm):
    llm.replies.extend([reply(GOOD_JSON[:40], finish_reason="length"), reply(GOOD_JSON)])

    fields = run_extract(llm)

    assert fields["agency"] == "Fei Yue"
    assert len(llm.calls) == 2


def test_invalid_json_retries_once_then_succeeds(llm):
    llm.replies.extend([reply("not json"), reply(GOOD_JSON)])

    fields = run_extract(llm)

    assert fields["summary"]
    assert len(llm.calls) == 2


def test_every_attempt_empty_returns_no_fields(llm):
    llm.replies.extend([reply(""), reply("")])

    assert run_extract(llm) == {}
    assert len(llm.calls) == 2


def test_each_call_is_bounded_by_a_timeout(llm):
    llm.replies.append(reply(GOOD_JSON))

    run_extract(llm)

    assert llm.calls[0]["timeout"] == llm.module.LLM_CALL_TIMEOUT_SECONDS


@pytest.fixture
def pipeline(llm, monkeypatch):
    """Load the pipeline with every external boundary replaced."""
    for name, attrs in {
        "app.clients.firestore": ("get_firestore_client", "update_scheme_entry"),
        "app.clients.onemap": ("PlanningAreaService",),
        "app.clients.slack_poster": ("post_to_slack_for_review",),
        "app.services.scraper": ("scrape_url",),
    }.items():
        stub = types.ModuleType(name)
        for attr in attrs:
            setattr(stub, attr, lambda *a, **k: None)
        monkeypatch.setitem(sys.modules, name, stub)
    return importlib.import_module("app.pipeline")


def run_pipeline(pipeline, monkeypatch, llm_fields):
    updates = []
    posted = []

    async def scrape(_url):
        return {"content": "Call us at hello@fycs.org.sg or 6123 4567. " + PAGE * 3, "logo_url": None, "error": None}

    async def extract(_text):
        return llm_fields

    monkeypatch.setattr(pipeline, "scrape_url", scrape)
    monkeypatch.setattr(pipeline, "extract_with_llm", extract)
    monkeypatch.setattr(pipeline, "get_firestore_client", lambda: object())
    monkeypatch.setattr(pipeline, "update_scheme_entry", lambda _db, _id, data: updates.append(data))
    monkeypatch.setattr(pipeline, "post_to_slack_for_review", lambda _id, data, _db: posted.append(data))

    result = asyncio.run(pipeline.process_scheme("doc1", "Fei Yue AAC", "https://fycs.org/x", {}))
    return result, updates[-1], posted[0]


def test_empty_llm_stage_is_flagged_for_review_not_completed(pipeline, monkeypatch):
    result, final_update, slack_data = run_pipeline(pipeline, monkeypatch, {})

    assert result["status"] == "needs_review"
    assert final_update["pipeline_status"] == "needs_review"
    assert "LLM extraction returned no fields" in final_update["pipeline_error"]
    assert slack_data["processing_status"] == "needs_review"


def test_populated_llm_stage_stays_completed(pipeline, monkeypatch):
    result, final_update, _ = run_pipeline(pipeline, monkeypatch, {"summary": "ok", "llm_description": "ok"})

    assert result["status"] == "completed"
    assert final_update["pipeline_error"] is None
