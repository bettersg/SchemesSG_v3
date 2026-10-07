"""Component contracts for weekly scheme link maintenance."""

import json

import pytest
from batch_jobs import run_link_check_and_reindex as link_job
from new_scheme import approval_handler
from new_scheme import trigger_new_scheme_pipeline as trigger
from slack_integration import slack as slack_module


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


def test_notion_failure_does_not_fail_link_check(mocker, fake_firestore, fake_slack_client):
    link = "https://example.gov.sg/ok"
    fake_firestore.seed("schemes", "scheme-ok", {"scheme": "OK", "link": link})
    metrics = mocker.patch.object(link_job, "append_metrics_row", side_effect=RuntimeError("Notion down"))

    result = _run_link_job(
        mocker,
        fake_firestore,
        fake_slack_client,
        {link: {"alive": True, "status_code": 200, "error": None}},
    )

    assert result["success"] is True
    metrics.assert_called_once_with(fake_firestore, 0, 0)
    assert len(fake_slack_client.posted_messages) == 1


def test_approved_link_restore_lists_the_scheme_and_the_checker_stops_flagging_it(
    mocker,
    mock_request,
    fake_firestore,
    fake_slack_client,
):
    link = "https://example.gov.sg/blocks-bots"
    fake_firestore.seed(
        "schemes",
        "scheme-1",
        {
            "scheme": "Blocks Bots Support",
            "link": link,
            "status": "inactive",
            "status_reason": "Dead link (hard_dead, 2 consecutive checks)",
            "link_check_status_code": 404,
            "link_check_error": "Not Found",
            "link_check_fail_streak": 2,
            "link_check_fail_class": "hard_dead",
        },
    )
    # What the Notion link queue sync writes for a "Checker wrong" verdict.
    entry = {"typeOfRequest": "restore", "targetSchemeId": "scheme-1", "Link": link, "userEmail": "vol@example.org"}
    fake_firestore.seed("schemeEntries", "entry-restore", entry)
    for module in (trigger, approval_handler):
        mocker.patch.object(module, "get_firestore_client", return_value=fake_firestore)
    mocker.patch.object(trigger, "get_slack_client", return_value=fake_slack_client)
    mocker.patch.object(trigger, "get_slack_channel", return_value="C-review")
    scrape = mocker.patch.object(trigger.requests, "post")
    mocker.patch.object(slack_module, "verify_slack_signature", return_value=True)
    mocker.patch.object(slack_module, "get_slack_client", return_value=fake_slack_client)

    # 1. The trigger posts a restore card without scraping; the scheme stays delisted.
    trigger.process_new_scheme_entry("entry-restore", entry)
    scrape.assert_not_called()
    card = fake_slack_client.posted_messages[-1]
    actions = next(block for block in card["blocks"] if block["type"] == "actions")
    assert [button["action_id"] for button in actions["elements"]] == ["approve_link_restore", "reject_link_restore"]
    assert "404 Not Found" in json.dumps(card["blocks"])
    assert fake_firestore.get_document("schemes", "scheme-1")["status"] == "inactive"

    # 2. A maintainer approves in Slack: listed again, failure history cleared, link verified.
    click = {
        "type": "block_actions",
        "user": {"id": "U-reviewer"},
        "container": {"channel_id": "C-review", "message_ts": "posted-1"},
        "actions": [{"action_id": "approve_link_restore", "value": "entry-restore"}],
    }
    response = slack_module.slack_interactive(
        mock_request(method="POST", json_data=click, headers={"Content-Type": "application/json"})
    )
    assert response.status_code == 200
    scheme = fake_firestore.get_document("schemes", "scheme-1")
    assert scheme["status"] == "active"
    assert (scheme["link_check_manual_verified_by"], scheme["link_check_manual_verified_link"]) == (
        "vol@example.org",
        link,
    )
    assert not {"status_reason", "link_check_fail_streak", "link_check_error", "link_suspect"} & set(scheme)
    entry_after = fake_firestore.get_document("schemeEntries", "entry-restore")
    assert (entry_after["Status"], entry_after["approved_by"]) == ("approved", "reviewer@example.com")
    assert "LINK RESTORE APPROVED" in json.dumps(fake_slack_client.updated_messages[-1])

    # 3. The weekly check keeps failing on this link, and never flags or delists it.
    health = {link: {"alive": False, "status_code": 404, "error": "Not Found"}}
    for _ in range(3):
        result = _run_link_job(mocker, fake_firestore, fake_slack_client, health)
        assert (result["link_check"]["dead_count"], result["link_check"]["suspect_count"]) == (0, 0)
    scheme = fake_firestore.get_document("schemes", "scheme-1")
    assert scheme["status"] == "active"
    assert not {"link_check_fail_streak", "link_suspect"} & set(scheme)


def test_verification_only_covers_the_link_a_maintainer_approved(mocker, fake_firestore, fake_slack_client):
    verified, new = "https://example.gov.sg/captcha", "https://example.gov.sg/new-home"
    fake_firestore.seed(
        "schemes",
        "scheme-1",
        {
            "scheme": "Captcha Support",
            "link": verified,
            "status": "active",
            "link_check_manual_verified_at": "2026-10-07",
            "link_check_manual_verified_link": "https://www.example.gov.sg/captcha/",
        },
    )
    failing = {"alive": False, "status_code": 404, "error": "Not Found"}

    # A maintainer corrects the details but keeps the link: still never flagged.
    fake_firestore.collection("schemes").document("scheme-1").update({"description": "Corrected"})
    result = _run_link_job(mocker, fake_firestore, fake_slack_client, {verified: failing})
    assert result["link_check"]["suspect_count"] == 0

    # The scheme gets a new link: that link is checked like any other.
    fake_firestore.collection("schemes").document("scheme-1").update({"link": new})
    result = _run_link_job(mocker, fake_firestore, fake_slack_client, {new: failing})
    assert result["link_check"]["suspect_count"] == 1
    assert fake_firestore.get_document("schemes", "scheme-1")["link_check_fail_streak"] == 1
