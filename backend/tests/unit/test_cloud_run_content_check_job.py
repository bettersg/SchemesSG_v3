"""Unit tests for Cloud Run Job monthly scheme content check and its Slack integration."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure scheme-processor is on sys.path so we can import app.run_content_check
SCHEME_PROCESSOR_DIR = Path(__file__).resolve().parents[2] / "scheme-processor"
if str(SCHEME_PROCESSOR_DIR) not in sys.path:
    sys.path.insert(0, str(SCHEME_PROCESSOR_DIR))

from app.run_content_check import (
    build_content_check_error_message,
    build_content_check_summary_message,
    get_slack_channel,
    get_slack_client,
    run_job_core,
)
from slack_sdk.errors import SlackApiError


def test_get_slack_client_and_channel(monkeypatch):
    """get_slack_client and get_slack_channel read environment variables and raise ValueError when unset."""
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_CHANNEL_ID", raising=False)

    with pytest.raises(ValueError, match="SLACK_BOT_TOKEN not set"):
        get_slack_client()

    with pytest.raises(ValueError, match="SLACK_CHANNEL_ID not set"):
        get_slack_channel()

    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_CHANNEL_ID", "C123456")

    client = get_slack_client()
    assert client.token == "xoxb-test-token"
    assert get_slack_channel() == "C123456"


def test_build_content_check_summary_message():
    """build_content_check_summary_message formats summary, flagged schemes, failures, and Notion sync."""
    results_summary = {
        "total_checked": 10,
        "outcomes": {
            "unchanged": 7,
            "flagged": 2,
            "baseline": 1,
            "skipped": 0,
            "scrape_failed": 0,
            "error": 0,
        },
        "duration_seconds": 125,
    }
    flagged_schemes = [
        {"doc_id": "s1", "scheme_name": "Scheme 1", "check_id": "c1", "detail": "eligibility changed"},
        {"doc_id": "s2", "scheme_name": "Scheme 2", "check_id": "c2", "detail": "contact updated"},
    ]
    failed_schemes = []

    msg = build_content_check_summary_message(
        results_summary, flagged_schemes, failed_schemes
    )

    assert "text" in msg
    assert "blocks" in msg
    assert "10 checked, 2 flagged" in msg["text"]

    blocks = msg["blocks"]
    assert any("Monthly Scheme Content Check Complete" in str(b) for b in blocks)
    assert any("Total schemes checked: *10*" in str(b) for b in blocks)
    assert any("Flagged Schemes (2)" in str(b) for b in blocks)
    assert any("Scheme 1" in str(b) for b in blocks)


def test_build_content_check_summary_message_with_failures():
    """build_content_check_summary_message includes failure blocks when errors occur."""
    results_summary = {
        "total_checked": 5,
        "outcomes": {
            "unchanged": 4,
            "flagged": 0,
            "baseline": 0,
            "skipped": 0,
            "scrape_failed": 1,
            "error": 0,
        },
        "duration_seconds": 45,
    }
    failed_schemes = [
        {"doc_id": "s3", "scheme_name": "Scheme 3", "outcome": "scrape_failed", "detail": "Timeout 30s"}
    ]

    msg = build_content_check_summary_message(
        results_summary, flagged_schemes=[], failed_schemes=failed_schemes
    )

    assert "1 failed" in msg["text"]
    assert any("Failed Checks (1)" in str(b) for b in msg["blocks"])
    assert any("Scheme 3" in str(b) for b in msg["blocks"])


def test_build_content_check_error_message():
    """build_content_check_error_message builds a clear failure alert."""
    msg = build_content_check_error_message("Database connection timed out")
    assert "Content Check Failed" in msg["text"]
    assert any("Database connection timed out" in str(b) for b in msg["blocks"])


def test_run_job_core_sends_slack_notification(monkeypatch):
    """run_job_core checks schemes and posts summary message to Slack."""
    mock_db = MagicMock()
    mock_store = MagicMock()

    mock_slack = MagicMock()
    fake_scheme_ids = ["s1"]

    monkeypatch.setattr(
        "app.run_content_check.check_single_scheme_in_job",
        lambda doc_id, store, now: {
            "scheme_id": doc_id,
            "scheme_name": "Test Scheme",
            "outcome": "flagged",
            "detail": "eligibility changed",
            "check_id": "chk-1",
        },
    )

    res = run_job_core(
        db=mock_db,
        store=mock_store,
        scheme_ids=fake_scheme_ids,
        concurrency=1,
        slack_client=mock_slack,
        slack_channel="C123456",
    )

    assert res["success"] is True
    assert res["total_checked"] == 1
    assert res["outcomes"]["flagged"] == 1
    assert len(res["flagged_schemes"]) == 1
    assert res["flagged_schemes"][0]["scheme_name"] == "Test Scheme"

    mock_slack.chat_postMessage.assert_called_once()
    call_kwargs = mock_slack.chat_postMessage.call_args[1]
    assert call_kwargs["channel"] == "C123456"
    assert "Monthly Scheme Content Check Complete" in str(call_kwargs["blocks"])


def test_run_job_core_handles_slack_failure(monkeypatch):
    """run_job_core still returns success even if Slack notification throws SlackApiError."""
    mock_db = MagicMock()
    mock_store = MagicMock()

    mock_slack = MagicMock()
    mock_slack.chat_postMessage.side_effect = SlackApiError("Slack rate limited", response={"error": "ratelimited"})

    monkeypatch.setattr(
        "app.run_content_check.check_single_scheme_in_job",
        lambda doc_id, store, now: {
            "scheme_id": doc_id,
            "scheme_name": "Test Scheme",
            "outcome": "unchanged",
            "detail": None,
            "check_id": None,
        },
    )

    res = run_job_core(
        db=mock_db,
        store=mock_store,
        scheme_ids=["s1"],
        concurrency=1,
        slack_client=mock_slack,
        slack_channel="C123456",
    )

    # Job still completes successfully despite Slack error
    assert res["success"] is True
    assert res["outcomes"]["unchanged"] == 1


def test_run_job_core_posts_error_to_slack_on_failure(monkeypatch):
    """run_job_core catches top-level fatal exception and posts error alert to Slack."""
    mock_db = MagicMock()
    mock_db.collection.side_effect = RuntimeError("Fatal firestore crash")

    mock_slack = MagicMock()

    res = run_job_core(
        db=mock_db,
        scheme_ids=None,
        slack_client=mock_slack,
        slack_channel="C123456",
    )

    assert res["success"] is False
    assert "Fatal firestore crash" in res["error"]
    mock_slack.chat_postMessage.assert_called_once()
    call_kwargs = mock_slack.chat_postMessage.call_args[1]
    assert "Content Check Failed" in call_kwargs["text"]

