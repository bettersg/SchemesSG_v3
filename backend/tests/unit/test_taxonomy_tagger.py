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
            seen["client"] = kwargs
            self.chat = types.SimpleNamespace(completions=Completions())
            seen["closed"] = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            seen["closed"] = True

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


def test_tagging_resource_can_differ_from_the_shared_one(monkeypatch):
    seen = {}
    payload = {"who_is_it_for": [], "what_it_gives": [], "scheme_type": [], "age_min": None, "age_max": None, "rationale": "x"}
    _fake_openai(monkeypatch, json.dumps(payload), seen)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://shared.example")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "shared-key")
    monkeypatch.setenv("AZURE_OPENAI_TAGGING_ENDPOINT", "https://tagging.example")
    monkeypatch.setenv("AZURE_OPENAI_TAGGING_API_KEY", "tagging-key")
    tagger.tag_scheme({"agency": "AIC"})
    assert seen["client"]["azure_endpoint"] == "https://tagging.example"
    assert seen["client"]["api_key"] == "tagging-key"


def test_client_has_an_explicit_timeout_and_bounded_retries(monkeypatch):
    seen = {}
    payload = {"who_is_it_for": [], "what_it_gives": [], "scheme_type": [], "age_min": None, "age_max": None, "rationale": "x"}
    _fake_openai(monkeypatch, json.dumps(payload), seen)
    tagger.tag_scheme({"agency": "AIC"})
    assert seen["client"]["timeout"] == tagger.TAGGING_TIMEOUT_SECONDS < 600
    assert seen["client"]["max_retries"] == 1
    # worst case must stay well inside the 300 s Cloud Run request, which scrape and extraction already use part of
    assert seen["client"]["timeout"] * (seen["client"]["max_retries"] + 1) <= 90
    assert seen["closed"] is True  # client is closed after each call


def test_tagging_resource_falls_back_to_the_shared_one(monkeypatch):
    seen = {}
    payload = {"who_is_it_for": [], "what_it_gives": [], "scheme_type": [], "age_min": None, "age_max": None, "rationale": "x"}
    _fake_openai(monkeypatch, json.dumps(payload), seen)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://shared.example")
    for name in ("AZURE_OPENAI_TAGGING_ENDPOINT", "AZURE_OPENAI_TAGGING_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    tagger.tag_scheme({"agency": "AIC"})
    assert seen["client"]["azure_endpoint"] == "https://shared.example"


def test_user_text_carries_source_text_and_the_prompt_never_says_elderly():
    text = tagger.build_user_text({"scheme": "S", "agency": "A", "description": "Source text", "llm_description": "Detailed text",
                                   "summary": "Short", "eligibility": "Aged 60+"})
    assert text.splitlines() == ["Scheme: S", "Agency: A", "Description: Source text", "Detailed description: Detailed text",
                                 "Summary: Short", "Eligibility: Aged 60+"]
    long = tagger.build_user_text({"scheme": "S", "description": "x" * 20000})
    assert len(long) < 12100  # source text is capped like the extraction call
    assert "Elderly" not in tagger.build_system_prompt().split("WHO_IS_IT_FOR terms")[0]
