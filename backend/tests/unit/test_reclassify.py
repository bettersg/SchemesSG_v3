"""Reclassification script: frozen-result reuse, old-vs-new diff, review flags and the write plan."""

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts/ncss_eval"))
sys.path.insert(0, str(BACKEND / "scheme-processor"))

import reclassify as rc  # noqa: E402

SCHEME = {
    "id": "a1", "scheme": "Legal clinic", "agency": "Law Society", "description": "Free legal advice.", "llm_description": None,
    "summary": None, "eligibility": "Low income", "status": None,
    "who_is_it_for": ["Elderly"], "what_it_gives": ["Referral services"], "scheme_type": ["Legal Aid", "Healthcare"],
}


def test_result_is_reused_only_while_input_and_prompt_are_unchanged():
    result = {"input_hash": rc.input_hash(SCHEME)}
    assert not rc.needs_classification(SCHEME, result)
    assert rc.needs_classification(SCHEME, result, force=True)
    assert rc.needs_classification(SCHEME, None)
    assert rc.needs_classification({**SCHEME, "description": "Edited text."}, result)


def test_old_tags_are_compared_in_the_new_vocabulary():
    old = rc.old_in_new_vocabulary(SCHEME)
    assert old["who_is_it_for"] == ["Seniors"]
    assert old["what_it_gives"] == ["Information and referral services", "Legal aid and services"]
    assert old["scheme_type"] == ["Healthcare"]
    same = {"who_is_it_for": ["Seniors"], "what_it_gives": old["what_it_gives"], "scheme_type": ["Healthcare"]}
    assert rc.changed_fields(SCHEME, same) == []
    assert rc.changed_fields(SCHEME, {**same, "scheme_type": ["Healthcare", "Financial Assistance"]}) == ["scheme_type"]


def test_new_tags_derive_age_bands_and_return_none_for_empty_fields():
    raw = json.dumps(
        {"who_is_it_for": ["Persons with disabilities (PWDs)"], "what_it_gives": ["Counselling"], "scheme_type": [],
         "age_min": 70, "age_max": None, "rationale": "r"})
    tags = rc.new_tags(raw)
    assert tags["who_is_it_for"] == ["Persons with disabilities (PWDs)", "Seniors"]
    assert tags["scheme_type"] is None and tags["age_min"] == 70


def test_review_flags_put_sensitive_schemes_first():
    result = {"who_is_it_for": ["Inmates", "Victims of abuse or harassment"], "what_it_gives": [], "scheme_type": ["Community Funding"]}
    flags = rc.review_flags({**SCHEME, "scheme_type": ["COVID-19 Support"]}, result)
    assert any("covid-19" in f for f in flags)
    assert "victims of abuse" in flags
    assert any(f.startswith("provisional:") for f in flags)
    assert rc.review_flags(SCHEME, {"who_is_it_for": ["Seniors"], "what_it_gives": ["Counselling"], "scheme_type": ["Healthcare"]}) == []
    assert rc.review_flags(SCHEME, {"who_is_it_for": None, "what_it_gives": None, "scheme_type": None}) == ["no tags"]


def test_apply_plan_only_touches_schemes_whose_tags_differ():
    snapshot = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": None, "scheme_type": ["Healthcare"]},
                "b": {"who_is_it_for": ["Youth"], "what_it_gives": ["Counselling"], "scheme_type": ["Healthcare"]},
                "c": {"who_is_it_for": ["Youth"], "what_it_gives": None, "scheme_type": None}}
    results = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": None, "scheme_type": ["Healthcare"]},
               "b": {"who_is_it_for": ["Youth"], "what_it_gives": ["Counselling", "Befriending services"], "scheme_type": ["Healthcare"]}}
    assert rc.apply_plan(snapshot, results) == {"b": {"what_it_gives": ["Counselling", "Befriending services"]}}


def test_term_counts_count_each_scheme_once():
    counts = rc.term_counts([{"who_is_it_for": ["Youth", "Youth"]}, {"who_is_it_for": ["Youth"]}, {}])
    assert counts["who_is_it_for"]["Youth"] == 2
