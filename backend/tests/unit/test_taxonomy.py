"""NCSS taxonomy: vendored copies stay in sync, aliases fail closed, category lists fit Firestore limits."""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
SP = BACKEND / "scheme-processor"
sys.path.insert(0, str(SP))

from app import taxonomy as tx  # noqa: E402  (scheme-processor copy)
from new_scheme import taxonomy as fx_tx  # noqa: E402  (functions copy)


def test_vendored_copies_are_identical():
    assert (SP / "app/taxonomy.py").read_text() == (BACKEND / "functions/new_scheme/taxonomy.py").read_text()
    assert (SP / "app/taxonomy_data.json").read_text() == (BACKEND / "functions/new_scheme/taxonomy_data.json").read_text()


def test_json_matches_generator():
    result = subprocess.run([sys.executable, "export_taxonomy.py", "--check"], cwd=BACKEND / "scripts/ncss_eval")
    assert result.returncode == 0, "run scripts/ncss_eval/export_taxonomy.py to regenerate taxonomy_data.json"


def test_every_alias_target_exists_and_no_alias_shadows_a_live_term():
    names = {f: set(tx.term_names(f)) for f in tx.FIELDS}
    for field, aliases in tx.TAXONOMY["legacy_aliases"].items():
        for old, spec in aliases.items():
            assert old not in names[field], f"alias {old} shadows a live term"
            for target in spec.get("to", []):
                assert target in names[field]
            for target_field, terms in spec.get("moved", {}).items():
                assert set(terms) <= names[target_field]


def test_terms_are_unique_per_field():
    for field in tx.FIELDS:
        names = tx.term_names(field)
        assert len(names) == len(set(names))


def test_normalize_exact_rename_and_alias():
    assert tx.normalize_terms("who_is_it_for", ["elderly", "Low income elderly"])[0] == ["Seniors", "Low income seniors"]
    assert tx.normalize_terms("what_it_gives", ["Referral services", "Information services"])[0] == [
        "Information and referral services"
    ]
    assert tx.normalize_terms("who_is_it_for", ["Persons with mental health issues"])[0] == [
        "Persons with mental health conditions"
    ]


def test_normalize_fails_closed_without_keyword_matching():
    # the old keyword-overlap fallback would have mapped these onto "Low income" / "Seniors" style terms
    matched, unmatched = tx.normalize_terms("who_is_it_for", ["low paid workers", "senior citizens", "bogus"])
    assert matched == []
    assert unmatched == ["low paid workers", "senior citizens", "bogus"]


def test_removed_terms_are_not_in_vocabulary():
    removed = {
        "what_it_gives": [
            "Protection against violence",
            "Child protection services",
            "Identification and safety tagging",
            "COVID-19 support",
            "Referral services",
            "Information services",
        ],
        "who_is_it_for": ["Need shelter", "Need food support", "Need mortgage support", "Individuals needing legal aid", "Elderly"],
    }
    for field, terms in removed.items():
        assert not set(terms) & set(tx.term_names(field))


def test_translate_legacy_moves_terms_across_fields():
    out = tx.translate_legacy(
        {
            "who_is_it_for": ["Elderly", "Need food support"],
            "what_it_gives": ["Referral services", "Protection against violence"],
            "scheme_type": ["Children", "Healthcare"],
        }
    )
    assert out["who_is_it_for"] == ["Seniors", "Children"]
    assert out["what_it_gives"] == ["Food support", "Information and referral services"]
    assert out["scheme_type"] == ["Protection from Violence", "Healthcare"]


def test_functions_copy_behaves_the_same():
    assert fx_tx.normalize_terms("who_is_it_for", ["Elderly"]) == tx.normalize_terms("who_is_it_for", ["Elderly"])


@pytest.mark.parametrize(
    "age_min,age_max,expected",
    [
        (None, None, None),
        (13, 21, {"Teenagers (13-17)", "Youth"}),
        (21, 22, {"Youth", "Adults"}),
        (59, 60, {"Adults", "Seniors"}),
        (60, None, {"Seniors"}),
        (0, 12, {"Infants and toddlers (0-3)", "Preschool children (4-6)", "Primary school children (7-12)", "Children"}),
    ],
)
def test_age_band_boundaries_are_inclusive(age_min, age_max, expected):
    assert tx.age_terms(age_min, age_max) == expected


def test_open_ended_adult_range_implies_seniors_only_if_model_chose_it():
    assert "Seniors" not in tx.apply_age_terms(["Adults"], 18, None)
    assert "Seniors" in tx.apply_age_terms(["Adults", "Seniors"], 18, None)
    assert tx.apply_age_terms(["Families", "Youth"], None, None) == ["Families", "Youth"]


def test_parents_come_from_the_static_table():
    assert tx.parents("who_is_it_for", ["Seniors with dementia"]) == {"age_group": ["Seniors"], "profile": ["Chronically ill"]}
    assert tx.parents("who_is_it_for", ["Facing end of life"]) == {"age_group": [], "profile": []}


def test_category_lists_fit_firestore_array_contains_any_limit():
    for category, values in tx.TAXONOMY["category_mapping"].items():
        assert len(values) <= 30, category
        assert len(values) == len(set(values)), category


def test_every_scheme_type_term_belongs_to_a_category():
    in_category = {v for values in tx.TAXONOMY["category_mapping"].values() for v in values}
    assert set(tx.term_names("scheme_type")) <= in_category


NCSS_14_OCT_REMOVED = [
    "Homelessness Support", "Vocational Training", "Legal Aid", "Residential Care", "Counselling and Emotional Support",
    "Traditional Chinese Medicine (TCM)", "Referral and Information Services", "Seniors Housing and Home Improvement",
    "COVID-19 Support", "Abuse/Family Violence", "Loss of Breadwinner Support", "Mental Health Rehabilitation",
]


def test_ncss_14_oct_scheme_types_are_removed_from_the_vocabulary():
    live = set(tx.term_names("scheme_type"))
    assert not live & set(NCSS_14_OCT_REMOVED)
    for flat in tx.TAXONOMY["category_mapping"].values():
        assert not set(flat) & set(NCSS_14_OCT_REMOVED)


def test_removed_scheme_types_move_to_the_ncss_destination():
    doc = {
        "scheme_type": ["Legal Aid", "Vocational Training", "Homelessness Support", "Referral and Information Services",
                        "Mental Health Rehabilitation", "Healthcare"],
        "what_it_gives": [],
        "who_is_it_for": [],
    }
    out = tx.translate_legacy(doc)
    assert out["what_it_gives"] == [
        "Legal aid and services", "Vocational training", "Information and referral services",
    ]
    assert out["who_is_it_for"] == ["Homeless"]
    assert out["scheme_type"] == ["Mental Health", "Healthcare"]


def test_programme_level_retags_leave_nothing_behind():
    out = tx.translate_legacy({"scheme_type": ["COVID-19 Support", "Abuse/Family Violence", "Loss of Breadwinner Support"]})
    assert out == {"who_is_it_for": [], "what_it_gives": [], "scheme_type": []}


def test_counselling_and_emotional_support_splits_by_intervention():
    out = tx.translate_legacy({"scheme_type": ["Counselling and Emotional Support"]})
    assert out["what_it_gives"] == ["Counselling", "Emotional care"]


def test_respite_care_rename_keeps_old_term_as_alias():
    assert "Respite care" in tx.term_names("what_it_gives")
    assert "Respite care/Caregiver support" not in tx.term_names("what_it_gives")
    assert tx.normalize_terms("what_it_gives", ["Respite care/Caregiver support"])[0] == ["Respite care"]
    assert tx.parents("what_it_gives", ["Respite care"]) == {"intervention": ["Care Services"]}


def test_ncss_14_oct_parent_changes():
    need = lambda name: tx.parents("scheme_type", [name])["need"]  # noqa: E731
    assert need("Protection from Violence") == ["Justice & Legal Protection"]
    assert need("Student Care Support") == ["Caregiving Support"]
    assert need("End-of-Life/Palliative Care") == ["Healthcare & Well-Being"]
    assert need("General Healthcare Subsidies") == ["Financial & Material Support"]
    for provisional in ("Transport Support", "Technology Support", "Community Funding"):
        assert tx.is_provisional("scheme_type", provisional)


def test_ncss_5_oct_profiles():
    assert tx.parents("who_is_it_for", ["Homeless"])["profile"] == ["Persons Experiencing Homelessness"]
    assert tx.parents("who_is_it_for", ["Inmates"]) == {"age_group": [], "profile": []}
    assert tx.is_provisional("who_is_it_for", "Inmates")
    assert "Victims of abuse or harassment" in tx.term_names("who_is_it_for")
