"""Regression tests for terminal scheme retirement and duplicate scanning."""

from unittest.mock import MagicMock

from new_scheme.new_scheme_blocks import build_scheme_retirement_review_message
from schemes.catalog import _get_listed_paginated_results, _keep_listed_schemes
from scripts.scan_duplicate_schemes import build_duplicate_report, normalize_name
from utils.catalog_pagination import PaginationResult
from utils.reindex_embeddings import delete_stale_embeddings


def test_retirement_review_message_uses_dedicated_actions():
    message = build_scheme_retirement_review_message(
        "entry-1",
        {
            "targetSchemeId": "duplicate",
            "mergedInto": "canonical",
            "retiredReason": "Duplicate record",
        },
        {"scheme": "Duplicate", "link": "https://old.example"},
        {"scheme": "Canonical", "link": "https://current.example"},
    )

    actions = next(block for block in message["blocks"] if block["type"] == "actions")
    assert [element["action_id"] for element in actions["elements"]] == [
        "approve_scheme_retirement",
        "reject_scheme_retirement",
    ]
    assert "canonical" in message["text"] or "canonical" in str(message["blocks"])


def test_retirement_pipeline_bypasses_scraping_and_duplicate_gate(mocker):
    from new_scheme import trigger_new_scheme_pipeline as mod

    db = MagicMock()
    entry_ref = MagicMock()
    target_ref = MagicMock()
    canonical_ref = MagicMock()
    target_snap = MagicMock(exists=True)
    target_snap.to_dict.return_value = {
        "scheme": "Duplicate",
        "link": "https://old.example",
    }
    canonical_snap = MagicMock(exists=True)
    canonical_snap.to_dict.return_value = {
        "scheme": "Canonical",
        "link": "https://current.example",
    }
    target_ref.get.return_value = target_snap
    canonical_ref.get.return_value = canonical_snap

    def collection(name):
        col = MagicMock()
        if name == "schemeEntries":
            col.document.return_value = entry_ref
        elif name == "schemes":
            col.document.side_effect = lambda doc_id: target_ref if doc_id == "duplicate" else canonical_ref
        return col

    db.collection.side_effect = collection
    mocker.patch.object(mod, "get_firestore_client", return_value=db)
    duplicate_check = mocker.patch.object(mod, "check_duplicate_scheme")
    processor_post = mocker.patch.object(mod.requests, "post")
    slack = MagicMock()
    slack.chat_postMessage.return_value = {"ok": True, "ts": "1.0"}
    mocker.patch.object(mod, "get_slack_client", return_value=slack)
    mocker.patch.object(mod, "get_slack_channel", return_value="C1")

    mod.process_new_scheme_entry(
        "entry-1",
        {
            "typeOfRequest": "retire",
            "targetSchemeId": "duplicate",
            "mergedInto": "canonical",
            "retiredReason": "Duplicate record",
        },
    )

    duplicate_check.assert_not_called()
    processor_post.assert_not_called()
    first_patch = entry_ref.update.call_args_list[0].args[0]
    assert first_patch["pipeline_status"] == "awaiting_approval"
    slack.chat_postMessage.assert_called_once()


def test_retirement_approval_updates_audit_and_deletes_embedding(mocker):
    from new_scheme import approval_handler as mod

    db = MagicMock()
    entry_ref = MagicMock()
    target_ref = MagicMock()
    canonical_ref = MagicMock()
    embedding_ref = MagicMock()

    entry_snap = MagicMock(exists=True)
    entry_snap.to_dict.return_value = {
        "typeOfRequest": "retire",
        "targetSchemeId": "duplicate",
        "mergedInto": "canonical",
        "retiredReason": "Duplicate record",
        "Scheme": "Duplicate",
    }
    entry_ref.get.return_value = entry_snap
    target_snap = MagicMock(exists=True)
    target_snap.to_dict.return_value = {"scheme": "Duplicate", "status": "inactive"}
    target_ref.get.return_value = target_snap
    canonical_snap = MagicMock(exists=True)
    canonical_snap.to_dict.return_value = {"scheme": "Canonical", "status": "active"}
    canonical_ref.get.return_value = canonical_snap

    def collection(name):
        col = MagicMock()
        if name == "schemeEntries":
            col.document.return_value = entry_ref
        elif name == "schemes":
            col.document.side_effect = lambda doc_id: target_ref if doc_id == "duplicate" else canonical_ref
        elif name == "schemes_embeddings":
            col.document.return_value = embedding_ref
        return col

    db.collection.side_effect = collection
    mocker.patch.object(mod, "get_firestore_client", return_value=db)
    slack = MagicMock()
    slack.users_info.return_value = {
        "ok": True,
        "user": {"profile": {"email": "reviewer@example.com"}},
    }

    mod.handle_scheme_retirement_approval(slack, "entry-1", "C1", "1.0", "U1")

    batch = db.batch.return_value
    target_patch = batch.update.call_args_list[0].args[1]
    entry_patch = batch.update.call_args_list[1].args[1]
    assert target_patch["status"] == "retired"
    assert target_patch["merged_into"] == "canonical"
    assert target_patch["retired_by"] == "reviewer@example.com"
    assert entry_patch["Status"] == "approved"
    assert entry_patch["reviewed_data"]["retiredReason"] == "Duplicate record"
    batch.delete.assert_called_once_with(embedding_ref)
    batch.commit.assert_called_once()


def test_catalog_filters_retired_schemes():
    result = _keep_listed_schemes(
        PaginationResult(
            data=[
                {"scheme_id": "legacy"},
                {"scheme_id": "active", "status": "active"},
                {"scheme_id": "inactive", "status": "inactive"},
                {"scheme_id": "retired", "status": "retired"},
            ]
        )
    )
    assert [item["scheme_id"] for item in result.data] == ["legacy", "active", "inactive"]


def test_delete_stale_embeddings_removes_non_searchable_ids():
    db = MagicMock()
    embedding_collection = MagicMock()
    embedding_collection.stream.return_value = [
        MagicMock(id="active"),
        MagicMock(id="retired"),
        MagicMock(id="orphan"),
    ]
    refs = {doc_id: MagicMock() for doc_id in ("active", "retired", "orphan")}
    embedding_collection.document.side_effect = refs.get
    db.collection.return_value = embedding_collection

    deleted = delete_stale_embeddings(db, {"active"})

    assert deleted == 2
    batch = db.batch.return_value
    batch.delete.assert_any_call(refs["retired"])
    batch.delete.assert_any_call(refs["orphan"])
    batch.commit.assert_called_once()


def test_duplicate_report_groups_urls_and_normalized_names():
    report = build_duplicate_report(
        [
            (
                "a",
                {
                    "scheme": "Scheme (EASE)",
                    "link": "https://www.example.gov.sg/ease/?ref=old",
                },
            ),
            (
                "b",
                {
                    "scheme": "Scheme - EASE",
                    "link": "https://example.gov.sg/ease",
                },
            ),
        ]
    )

    assert len(report["url_clusters"]) == 1
    assert len(report["same_name_clusters"]) == 1
    assert normalize_name(" EASE! ") == "ease"


def test_weekly_link_check_skips_retired_schemes(mocker):
    from batch_jobs import run_link_check_and_reindex as mod

    active_doc = MagicMock(id="active")
    active_doc.to_dict.return_value = {
        "scheme": "Active",
        "link": "https://active.example",
        "status": "active",
    }
    retired_doc = MagicMock(id="retired")
    retired_doc.to_dict.return_value = {
        "scheme": "Retired",
        "link": "https://retired.example",
        "status": "retired",
    }

    db = MagicMock()
    schemes_collection = MagicMock()
    schemes_collection.stream.return_value = [active_doc, retired_doc]
    db.collection.return_value = schemes_collection
    check = mocker.patch.object(
        mod,
        "check_single_scheme",
        return_value=(
            "active",
            active_doc.to_dict.return_value,
            {"alive": True, "status_code": 200},
        ),
    )
    mocker.patch.object(
        mod,
        "reindex_embeddings",
        return_value={"success": True, "indexed_schemes": 1},
    )
    slack = MagicMock()
    mocker.patch.object(mod, "get_slack_client", return_value=slack)
    mocker.patch.object(mod, "get_slack_channel", return_value="C1")

    result = mod.run_link_check_and_reindex_core(db)

    check.assert_called_once_with("active", active_doc.to_dict.return_value)
    assert result["link_check"]["retired_skipped"] == 1
    assert result["link_check"]["total_checked"] == 1


def test_catalog_refills_page_after_skipping_retired(mocker):
    paginated = mocker.patch(
        "schemes.catalog.get_paginated_results",
        side_effect=[
            PaginationResult(
                data=[
                    {"scheme_id": "retired", "status": "retired"},
                    {"scheme_id": "active-a", "status": "active"},
                ],
                next_cursor="next",
                has_more=True,
            ),
            PaginationResult(
                data=[{"scheme_id": "active-b", "status": "active"}],
                has_more=False,
            ),
        ],
    )

    result = _get_listed_paginated_results(MagicMock(), limit=2)

    assert [item["scheme_id"] for item in result.data] == ["active-a", "active-b"]
    assert paginated.call_count == 2
    assert paginated.call_args_list[1].kwargs["cursor"] == "next"
