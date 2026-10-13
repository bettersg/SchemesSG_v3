"""Integration contract tests for link discovery batch job."""

from unittest.mock import MagicMock

from batch_jobs import run_link_discovery_agent as discovery_job
from batch_jobs.run_link_discovery_agent import URLFinderAgentResponse


def test_link_discovery_identifies_broken_schemes_and_updates_db(
    mocker,
    fake_firestore,
):
    """Link discovery finds inactive and suspect schemes, runs agent, and updates Firestore."""
    # Seed schemes
    fake_firestore.seed(
        "schemes",
        "scheme-inactive",
        {
            "scheme": "Financial Assistance Scheme",
            "link": "https://broken.gov.sg/fas",
            "status": "inactive",
            "status_reason": "Dead link (hard_dead, 2 consecutive checks)",
        },
    )
    fake_firestore.seed(
        "schemes",
        "scheme-suspect",
        {
            "scheme": "Elderly Care Scheme",
            "link": "https://suspect.gov.sg/elderly",
            "status": "active",
            "link_suspect": True,
        },
    )
    fake_firestore.seed(
        "schemes",
        "scheme-retired",
        {
            "scheme": "Retired Scheme",
            "link": "https://retired.gov.sg/scheme",
            "status": "retired",
        },
    )
    fake_firestore.seed(
        "schemes",
        "scheme-healthy",
        {
            "scheme": "Healthy Active Scheme",
            "link": "https://healthy.gov.sg/scheme",
            "status": "active",
        },
    )

    def mock_agent_call(scheme_name, previous_link, session_id):
        if "Financial Assistance" in scheme_name:
            return URLFinderAgentResponse(
                url="https://new.gov.sg/fas",
                summary="Found updated official FAS portal page",
                evidence_urls=["https://new.gov.sg/fas/about"],
            )
        else:
            return URLFinderAgentResponse(
                url=None,
                summary="Programme discontinued or not found",
                evidence_urls=[],
            )

    mocker.patch.object(discovery_job, "call_link_check_agent", side_effect=mock_agent_call)

    result = discovery_job.run_link_discovery_core(
        db=fake_firestore,
        max_parallel_jobs=2,
        include_suspect=True,
        update_db=True,
    )

    assert result["success"] is True
    assert result["discovery"]["total_checked"] == 2
    assert result["discovery"]["found_count"] == 1
    assert result["discovery"]["not_found_count"] == 1
    assert result["discovery"]["error_count"] == 0

    # Verify Firestore was updated for the found scheme
    stored_fas = fake_firestore.get_document("schemes", "scheme-inactive")
    assert stored_fas["discovered_link"] == "https://new.gov.sg/fas"
    assert stored_fas["discovered_link_summary"] == "Found updated official FAS portal page"
    assert stored_fas["discovered_link_evidence"] == ["https://new.gov.sg/fas/about"]
    assert "discovered_link_checked_at" in stored_fas

    # Verify Firestore was updated for the not-found scheme
    stored_elderly = fake_firestore.get_document("schemes", "scheme-suspect")
    assert "discovered_link" not in stored_elderly
    assert stored_elderly["discovered_link_summary"] == "Programme discontinued or not found"
    assert "discovered_link_checked_at" in stored_elderly

    # Verify retired and healthy schemes were untouched
    stored_retired = fake_firestore.get_document("schemes", "scheme-retired")
    assert "discovered_link_checked_at" not in stored_retired
    stored_healthy = fake_firestore.get_document("schemes", "scheme-healthy")
    assert "discovered_link_checked_at" not in stored_healthy


def test_link_discovery_respects_max_parallel_jobs_parameter(
    mocker,
    fake_firestore,
):
    """Link discovery bounds ThreadPoolExecutor max_workers to max_parallel_jobs."""
    # Seed 5 inactive schemes
    for i in range(5):
        fake_firestore.seed(
            "schemes",
            f"scheme-{i}",
            {
                "scheme": f"Scheme {i}",
                "link": f"https://broken.gov.sg/{i}",
                "status": "inactive",
            },
        )

    mock_executor_cls = mocker.patch("batch_jobs.run_link_discovery_agent.ThreadPoolExecutor")
    mock_instance = MagicMock()
    mock_executor_cls.return_value.__enter__.return_value = mock_instance

    # Return empty futures so it terminates cleanly
    mock_instance.submit.return_value = MagicMock()
    mocker.patch("batch_jobs.run_link_discovery_agent.as_completed", return_value=[])

    discovery_job.run_link_discovery_core(
        db=fake_firestore,
        max_parallel_jobs=2,
    )

    mock_executor_cls.assert_called_once_with(max_workers=2)


def test_link_discovery_handles_errors_gracefully(
    mocker,
    fake_firestore,
):
    """Link discovery continues processing when individual scheme check fails."""
    fake_firestore.seed(
        "schemes",
        "scheme-failing",
        {
            "scheme": "Failing Scheme",
            "link": "https://broken.gov.sg/fail",
            "status": "inactive",
        },
    )

    def failing_agent_call(scheme_name, previous_link, session_id):
        raise RuntimeError("Network timeout connecting to LLM")

    mocker.patch.object(discovery_job, "call_link_check_agent", side_effect=failing_agent_call)

    result = discovery_job.run_link_discovery_core(
        db=fake_firestore,
        max_parallel_jobs=1,
    )

    assert result["success"] is True
    assert result["discovery"]["total_checked"] == 1
    assert result["discovery"]["error_count"] == 1
    assert result["discovery"]["found_count"] == 0


def test_scheduled_link_discovery_agent_event_handler(mocker):
    """Scheduled function unpacks event and calls core logic."""
    from flask import Flask, request

    mock_core = mocker.patch(
        "batch_jobs.run_link_discovery_agent.run_link_discovery_core",
        return_value={"success": True, "discovery": {"total_checked": 0}},
    )
    app = Flask(__name__)
    with app.test_request_context(headers={"X-CloudScheduler-ScheduleTime": "2026-10-13T10:00:00Z"}):
        discovery_job.scheduled_link_discovery_agent(request)
    mock_core.assert_called_once()

