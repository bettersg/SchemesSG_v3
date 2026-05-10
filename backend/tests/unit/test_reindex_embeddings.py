"""Unit tests for utils.reindex_embeddings.build_desc_booster."""

import pandas as pd

from utils.reindex_embeddings import build_desc_booster


def test_list_field_is_joined_with_comma_space():
    row = pd.Series({"who_is_it_for": ["Elderly", "Caregivers"]})
    assert build_desc_booster(row) == "Elderly, Caregivers"


def test_scalar_string_is_passed_through():
    row = pd.Series({"scheme": "Silver Support Scheme"})
    assert build_desc_booster(row) == "Silver Support Scheme"


def test_none_scalar_is_skipped():
    row = pd.Series({"scheme": None})
    assert build_desc_booster(row) == ""


def test_nan_scalar_is_skipped():
    row = pd.Series({"scheme": float("nan")})
    assert build_desc_booster(row) == ""


def test_empty_list_is_skipped():
    row = pd.Series({"who_is_it_for": []})
    assert build_desc_booster(row) == ""


def test_list_filters_out_none_empty_and_whitespace_entries():
    row = pd.Series({"who_is_it_for": [None, "", "  ", "Elderly"]})
    assert build_desc_booster(row) == "Elderly"


def test_row_missing_all_loop_fields_returns_empty_string():
    row = pd.Series({"doc_id": "abc123", "unrelated_field": "ignored"})
    assert build_desc_booster(row) == ""


def test_realistic_mixed_row_combines_scalars_and_lists():
    row = pd.Series(
        {
            "scheme": "Silver Support Scheme",
            "agency": "CPF Board",
            "llm_description": "Monthly payout for lower-income seniors.",
            "who_is_it_for": ["Elderly", "Low-income"],
            "what_it_gives": ["Monthly cash payout"],
            "scheme_type": ["Financial Assistance"],
            "service_area": "Singapore",
        }
    )
    result = build_desc_booster(row)
    assert "Silver Support Scheme" in result
    assert "CPF Board" in result
    assert "Monthly payout for lower-income seniors." in result
    assert "Elderly, Low-income" in result
    assert "Monthly cash payout" in result
    assert "Financial Assistance" in result
    assert "Singapore" in result
