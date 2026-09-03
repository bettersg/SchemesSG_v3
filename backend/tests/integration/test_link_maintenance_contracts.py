"""Component contracts for weekly scheme link maintenance."""

import pytest
from batch_jobs import run_link_check_and_reindex as link_job


def _run_link_job(mocker, fake_firestore, fake_slack_client, health_by_url):
    def check_link(url):
        return dict(health_by_url[url])

    mocker.patch.object(link_job, "check_link_health", side_effect=check_link)
    mocker.patch.object(link_job.time, "sleep", return_value=None)
    mocker.patch.object(
        link_job,
        "reindex_embeddings",
        return_value={"success": True, "indexed_schemes": 1},
    )
    mocker.patch.object(link_job, "get_slack_client", return_value=fake_slack_client)
    mocker.patch.object(link_job, "get_slack_channel", return_value="C-maintenance")
    return link_job.run_link_check_and_reindex_core(fake_firestore)


def test_healthy_link_restores_inactive_scheme_and_clears_quarantine(
    mocker,
    fake_firestore,
    fake_slack_client,
):
    link = "https://example.gov.sg/restored"
    fake_firestore.seed(
        "schemes",
        "scheme-restored",
        {
            "scheme": "Restored Support",
            "link": link,
            "status": "inactive",
            "status_reason": "Dead link",
            "status_updated_at": "earlier",
            "link_check_error": "Not Found",
            "link_check_fail_streak": 2,
            "link_check_fail_class": "hard_dead",
            "link_suspect": True,
        },
    )

    result = _run_link_job(
        mocker,
        fake_firestore,
        fake_slack_client,
        {link: {"alive": True, "status_code": 200, "error": None}},
    )

    assert result["success"] is True
    assert result["link_check"]["restored_count"] == 1
    stored = fake_firestore.get_document("schemes", "scheme-restored")
    assert stored["link_check_status_code"] == 200
    for cleared_field in (
        "status",
        "status_reason",
        "status_updated_at",
        "link_check_error",
        "link_check_fail_streak",
        "link_check_fail_class",
        "link_suspect",
    ):
        assert cleared_field not in stored


@pytest.mark.parametrize(
    ("status_code", "expected_class"),
    [(404, "hard_dead"), (503, "transient")],
)
def test_failed_link_is_quarantined_before_inactivation(
    status_code,
    expected_class,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    link = "https://example.gov.sg/unavailable"
    fake_firestore.seed(
        "schemes",
        "scheme-suspect",
        {
            "scheme": "Unavailable Support",
            "link": link,
            "status": "active",
        },
    )

    result = _run_link_job(
        mocker,
        fake_firestore,
        fake_slack_client,
        {
            link: {
                "alive": False,
                "status_code": status_code,
                "error": f"HTTP {status_code}",
            }
        },
    )

    assert result["success"] is True
    assert result["link_check"]["dead_count"] == 0
    assert result["link_check"]["suspect_count"] == 1
    assert result["link_check"]["suspect_links"][0]["fail_class"] == expected_class
    stored = fake_firestore.get_document("schemes", "scheme-suspect")
    assert stored["status"] == "active"
    assert stored["link_suspect"] is True
    assert stored["link_check_fail_streak"] == 1
    assert stored["link_check_fail_class"] == expected_class


def test_repeated_hard_failure_inactivates_scheme(
    mocker,
    fake_firestore,
    fake_slack_client,
):
    link = "https://example.gov.sg/gone"
    fake_firestore.seed(
        "schemes",
        "scheme-gone",
        {
            "scheme": "Gone Support",
            "link": link,
            "status": "active",
            "link_suspect": True,
            "link_check_fail_streak": 1,
            "link_check_fail_class": "hard_dead",
        },
    )

    result = _run_link_job(
        mocker,
        fake_firestore,
        fake_slack_client,
        {link: {"alive": False, "status_code": 410, "error": "Gone"}},
    )

    assert result["success"] is True
    assert result["link_check"]["dead_count"] == 1
    assert result["link_check"]["suspect_count"] == 0
    stored = fake_firestore.get_document("schemes", "scheme-gone")
    assert stored["status"] == "inactive"
    assert stored["link_check_fail_streak"] == 2
    assert stored["link_check_fail_class"] == "hard_dead"
    assert "link_suspect" not in stored


def test_retired_scheme_is_excluded_from_link_maintenance(
    mocker,
    fake_firestore,
    fake_slack_client,
):
    active_link = "https://example.gov.sg/active"
    retired = {
        "scheme": "Retired Support",
        "link": "https://example.gov.sg/retired",
        "status": "retired",
        "retired_reason": "Duplicate",
    }
    fake_firestore.seed(
        "schemes",
        "scheme-active",
        {"scheme": "Active Support", "link": active_link, "status": "active"},
    )
    fake_firestore.seed("schemes", "scheme-retired", retired)

    result = _run_link_job(
        mocker,
        fake_firestore,
        fake_slack_client,
        {active_link: {"alive": True, "status_code": 200, "error": None}},
    )

    assert result["success"] is True
    assert result["link_check"]["total_checked"] == 1
    assert result["link_check"]["retired_skipped"] == 1
    assert fake_firestore.get_document("schemes", "scheme-retired") == retired
