"""Unit tests for the monthly scheme content change check batch job (run_content_check.py)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from batch_jobs import run_content_check as content_job


class FakeDoc:
    def __init__(self, doc_id: str, data: dict = None):
        self.id = doc_id
        self._data = data or {}

    def to_dict(self):
        return self._data


class FakeCollection:
    def __init__(self, docs: list):
        self._docs = docs

    def stream(self):
        return iter(self._docs)


class FakeDb:
    def __init__(self, docs: list = None):
        self._docs = docs or []

    def collection(self, name: str):
        if name == "schemes":
            return FakeCollection(self._docs)
        return FakeCollection([])


def test_check_single_scheme_calls_check_scheme_locally(monkeypatch):
    """check_single_scheme runs check_scheme locally when review_fn or scrape_fn is passed."""
    mock_check_scheme = AsyncMock(
        return_value={
            "scheme_id": "s1",
            "outcome": "baseline",
            "detail": "1 page(s) saved",
            "check_id": None,
        }
    )
    monkeypatch.setattr(content_job, "check_scheme", mock_check_scheme)

    mock_store = MagicMock()
    mock_scrape = AsyncMock()
    mock_review = AsyncMock()

    result = content_job.check_single_scheme(
        doc_id="s1",
        store=mock_store,
        scrape_fn=mock_scrape,
        review_fn=mock_review,
    )

    assert result["outcome"] == "baseline"
    mock_check_scheme.assert_awaited_once_with("s1", mock_store, mock_scrape, review=mock_review)


def test_check_single_scheme_via_processor(monkeypatch):
    """check_single_scheme delegates to scheme-processor when processor_url is configured."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "scheme_id": "s1",
                "outcome": "unchanged",
                "detail": None,
                "check_id": None,
            }
        ]
    }
    mock_post = MagicMock(return_value=mock_response)
    monkeypatch.setattr(content_job.requests, "post", mock_post)

    result = content_job.check_single_scheme(
        doc_id="s1",
        processor_url="http://scheme-processor:8081",
    )

    assert result["outcome"] == "unchanged"
    mock_post.assert_called_once_with(
        "http://scheme-processor:8081/content-check",
        json={"scheme_ids": ["s1"]},
        headers={"Content-Type": "application/json"},
        timeout=300,
    )


def test_check_single_scheme_raises_when_no_scraper(monkeypatch):
    """check_single_scheme raises ValueError when scrape_fn and default_scrape are None."""
    monkeypatch.setattr(content_job, "default_scrape", None)
    monkeypatch.setattr(content_job, "PROCESSOR_SERVICE_URL", "")
    mock_store = MagicMock()

    with pytest.raises(ValueError, match="No scraper function available"):
        content_job.check_single_scheme(doc_id="s1", store=mock_store, scrape_fn=None, processor_url="")


def test_run_content_check_core_empty_schemes():
    """run_content_check_core returns success immediately when no schemes are found."""
    db = FakeDb([])
    result = content_job.run_content_check_core(db=db, scheme_ids=[])

    assert result["success"] is True
    assert result["total_checked"] == 0
    assert result["outcomes"]["baseline"] == 0
    assert result["flagged_schemes"] == []
    assert result["failed_schemes"] == []


def test_run_content_check_core_with_scheme_ids(monkeypatch):
    """run_content_check_core processes provided scheme_ids and aggregates outcomes."""
    mock_results = {
        "s1": {"scheme_id": "s1", "outcome": "baseline", "detail": "saved", "check_id": None},
        "s2": {"scheme_id": "s2", "outcome": "unchanged", "detail": None, "check_id": None},
        "s3": {"scheme_id": "s3", "outcome": "flagged", "detail": "1 suggestion", "check_id": "chk-1"},
        "s4": {"scheme_id": "s4", "outcome": "skipped", "detail": "status inactive", "check_id": None},
        "s5": {"scheme_id": "s5", "outcome": "scrape_failed", "detail": "timeout", "check_id": None},
    }

    def fake_check_single(doc_id, *args, **kwargs):
        return mock_results[doc_id]

    monkeypatch.setattr(content_job, "check_single_scheme", fake_check_single)
    db = FakeDb([])

    result = content_job.run_content_check_core(
        db=db,
        scheme_ids=["s1", "s2", "s3", "s4", "s5"],
    )

    assert result["success"] is True
    assert result["total_checked"] == 5
    assert result["outcomes"]["baseline"] == 1
    assert result["outcomes"]["unchanged"] == 1
    assert result["outcomes"]["flagged"] == 1
    assert result["outcomes"]["skipped"] == 1
    assert result["outcomes"]["scrape_failed"] == 1
    assert len(result["flagged_schemes"]) == 1
    assert result["flagged_schemes"][0]["doc_id"] == "s3"
    assert result["flagged_schemes"][0]["check_id"] == "chk-1"
    assert len(result["failed_schemes"]) == 1
    assert result["failed_schemes"][0]["doc_id"] == "s5"


def test_run_content_check_core_streams_from_firestore(monkeypatch):
    """When scheme_ids is omitted, schemes are streamed from db.collection('schemes')."""
    docs = [FakeDoc("s1"), FakeDoc("s2")]
    db = FakeDb(docs)

    monkeypatch.setattr(
        content_job,
        "check_single_scheme",
        lambda doc_id, *args, **kwargs: {
            "scheme_id": doc_id,
            "outcome": "unchanged",
            "detail": None,
            "check_id": None,
        },
    )

    result = content_job.run_content_check_core(db=db)

    assert result["success"] is True
    assert result["total_checked"] == 2
    assert result["outcomes"]["unchanged"] == 2


def test_run_content_check_core_handles_worker_exception(monkeypatch):
    """A worker exception does not crash the batch job and records outcome as error."""

    def fake_check(doc_id, *args, **kwargs):
        if doc_id == "bad":
            raise RuntimeError("Network crash")
        return {"scheme_id": doc_id, "outcome": "unchanged", "detail": None, "check_id": None}

    monkeypatch.setattr(content_job, "check_single_scheme", fake_check)
    db = FakeDb([])

    result = content_job.run_content_check_core(db=db, scheme_ids=["good", "bad"])

    assert result["success"] is True
    assert result["total_checked"] == 2
    assert result["outcomes"]["unchanged"] == 1
    assert result["outcomes"]["error"] == 1
    assert len(result["failed_schemes"]) == 1
    assert result["failed_schemes"][0]["doc_id"] == "bad"
    assert "Network crash" in result["failed_schemes"][0]["detail"]


def test_run_content_check_core_top_level_error(monkeypatch):
    """Top-level database/setup failures return success=False and the error message."""
    mock_db = MagicMock()
    mock_db.collection.side_effect = RuntimeError("Firestore unavailable")

    result = content_job.run_content_check_core(db=mock_db)

    assert result["success"] is False
    assert "Firestore unavailable" in result["error"]


def test_scheduled_content_check(monkeypatch):
    """scheduled_content_check invokes run_content_check_core."""
    mock_run = MagicMock(return_value={"success": True, "total_checked": 0})
    monkeypatch.setattr(content_job, "run_content_check_core", mock_run)

    event = SimpleNamespace(schedule_time="2026-11-01T10:00:00Z")
    content_job.scheduled_content_check.__wrapped__(event)

    mock_run.assert_called_once_with()
