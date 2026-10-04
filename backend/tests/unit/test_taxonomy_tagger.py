"""Taxonomy tagging call: strict schema + effort actually reach litellm, output is validated, failures stay contained."""

import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scheme-processor"))

from app.services import taxonomy_tagger as tagger  # noqa: E402


def _fake_openai(monkeypatch, content, seen):
    class Completions:
        def create(self, **kwargs):
            seen.update(kwargs)
            message = types.SimpleNamespace(content=content)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)], usage=None)

    class FakeAzureOpenAI:
        def __init__(self, **kwargs):
            self.chat = types.SimpleNamespace(completions=Completions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(AzureOpenAI=FakeAzureOpenAI))


def test_call_sends_strict_schema_and_effort(monkeypatch):
    seen = {}
    payload = {"who_is_it_for": ["Seniors"], "what_it_gives": [], "scheme_type": [], "age_min": 65, "age_max": None, "rationale": "x"}
    _fake_openai(monkeypatch, json.dumps(payload), seen)
    tagger.tag_scheme({"agency": "AIC", "summary": "Seniors support"})
    assert seen["response_format"]["json_schema"]["strict"] is True
    assert seen["reasoning_effort"] == "medium"
    assert seen["model"] == "gpt-6-luna"


def test_schema_enums_are_the_current_vocabulary():
    props = tagger.TAGGING_SCHEMA["schema"]["properties"]
    assert "Seniors" in props["who_is_it_for"]["items"]["enum"]
    assert "Elderly" not in props["who_is_it_for"]["items"]["enum"]
    assert "Referral services" not in props["what_it_gives"]["items"]["enum"]


def test_prompt_carries_definitions_and_the_mental_health_rule():
    prompt = tagger.build_system_prompt()
    assert "Mental health conditions are NOT disabilities" in prompt
    assert "- Seniors:" in prompt


def test_parse_applies_code_derived_age_bands_and_returns_none_for_empty():
    raw = json.dumps({"who_is_it_for": ["Youth"], "what_it_gives": [], "scheme_type": [], "age_min": 15, "age_max": 25, "rationale": ""})
    out = tagger.parse_tagging_response(raw)
    assert out["who_is_it_for"] == ["Teenagers (13-17)", "Youth", "Adults"]
    assert out["what_it_gives"] is None and out["scheme_type"] is None


def test_out_of_vocabulary_values_are_dropped_not_guessed():
    raw = json.dumps({"who_is_it_for": ["senior citizens"], "what_it_gives": ["Food support"], "scheme_type": [], "age_min": None, "age_max": None, "rationale": ""})
    out = tagger.parse_tagging_response(raw)
    assert out["who_is_it_for"] is None and out["what_it_gives"] == ["Food support"]


def test_empty_response_raises(monkeypatch):
    _fake_openai(monkeypatch, "", {})
    with pytest.raises(ValueError):
        tagger.tag_scheme({"agency": "x"})
