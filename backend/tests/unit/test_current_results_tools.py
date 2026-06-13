"""Unit tests for deterministic current-result refinement tools."""

import importlib.util
from pathlib import Path


CURRENT_RESULTS_PATH = (
    Path(__file__).resolve().parents[2]
    / "functions"
    / "agent"
    / "tools"
    / "current_results.py"
)
spec = importlib.util.spec_from_file_location("current_results", CURRENT_RESULTS_PATH)
current_results = importlib.util.module_from_spec(spec)
spec.loader.exec_module(current_results)


def _scheme(scheme_id: str, name: str, summary: str) -> dict:
    return {
        "scheme_id": scheme_id,
        "scheme": name,
        "agency": "Agency",
        "summary": summary,
        "description": summary,
    }


def test_select_current_schemes_by_position_keeps_ranked_prefix(mocker):
    schemes = [
        _scheme("s1", "First", "general support"),
        _scheme("s2", "Second", "health support"),
        _scheme("s3", "Third", "education support"),
    ]
    mocker.patch.object(current_results, "_retrieve_current_schemes", return_value=schemes)
    mocker.patch.object(current_results, "_save_current_schemes_result", return_value="cutoff-doc")
    mocker.patch.object(current_results, "_emit_action_message")
    emitted = mocker.patch.object(current_results, "_emit_schemes_update")

    result = current_results.select_current_schemes_by_position("source-doc", 2)

    assert [scheme["scheme_id"] for scheme in result["schemes"]] == ["s1", "s2"]
    assert result["docID"] == "cutoff-doc"
    assert result["result_count"] == 2
    emitted.assert_called_once_with(schemes[:2])


def test_search_current_schemes_bm25_searches_within_existing_results(mocker):
    schemes = [
        _scheme("s1", "Cash Support", "cash and grocery vouchers"),
        _scheme("s2", "Medication Help", "medication subsidies and pharmacy support"),
        _scheme("s3", "Medical Transport", "transport to clinics"),
    ]
    mocker.patch.object(current_results, "_retrieve_current_schemes", return_value=schemes)
    mocker.patch.object(current_results, "_save_current_schemes_result", return_value="bm25-doc")
    mocker.patch.object(current_results, "_emit_action_message")
    emitted = mocker.patch.object(current_results, "_emit_schemes_update")

    result = current_results.search_current_schemes_bm25("source-doc", "medication pharmacy", 1)

    assert [scheme["scheme_id"] for scheme in result["schemes"]] == ["s2"]
    assert result["docID"] == "bm25-doc"
    assert result["result_count"] == 1
    emitted_schemes = emitted.call_args.args[0]
    assert [scheme["scheme_id"] for scheme in emitted_schemes] == ["s2"]
    assert "bm25_score" in emitted_schemes[0]


def test_search_current_schemes_bm25_returns_empty_when_no_keyword_match(mocker):
    schemes = [
        _scheme("s1", "Cash Support", "cash and grocery vouchers"),
        _scheme("s2", "Transport Help", "bus and clinic transport"),
    ]
    mocker.patch.object(current_results, "_retrieve_current_schemes", return_value=schemes)
    mocker.patch.object(current_results, "_save_current_schemes_result", return_value="empty-doc")
    mocker.patch.object(current_results, "_emit_action_message")
    emitted = mocker.patch.object(current_results, "_emit_schemes_update")

    result = current_results.search_current_schemes_bm25("source-doc", "medication", 5)

    assert result["schemes"] == []
    assert result["result_count"] == 0
    emitted.assert_called_once_with([])
