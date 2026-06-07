"""Integration tests for approval handler's update-in-place branch."""

import json
from typing import Optional


def _approval_event(scheme_url: str = "https://example.com/replacement") -> dict:
    return {
        "user": {"id": "U123"},
        "view": {
            "private_metadata": json.dumps(
                {"doc_id": "entry-1", "channel": "C1", "message_ts": "1.0"}
            ),
            "state": {
                "values": {
                    "scheme_name_block": {
                        "scheme_name": {"value": "Existing Scheme"}
                    },
                    "scheme_url_block": {"scheme_url": {"value": scheme_url}},
                    "agency_block": {"agency": {"value": "SkillsFuture SG"}},
                    "image_url_block": {"image_url": {"value": ""}},
                    "address_block": {"address": {"value": ""}},
                    "phone_block": {"phone": {"value": ""}},
                    "email_block": {"email": {"value": ""}},
                    "planning_area_block": {"planning_area": {"value": ""}},
                    "who_is_it_for_block": {
                        "who_is_it_for": {"selected_options": []}
                    },
                    "what_it_gives_block": {
                        "what_it_gives": {"selected_options": []}
                    },
                    "scheme_type_block": {
                        "scheme_type": {"selected_options": []}
                    },
                    "llm_description_block": {
                        "llm_description": {"value": "Updated description."}
                    },
                    "eligibility_block": {"eligibility": {"value": ""}},
                    "how_to_apply_block": {"how_to_apply": {"value": ""}},
                }
            },
        },
    }


def _entry_dict(
    type_of_request: str = "update",
    target_scheme_id: Optional[str] = "scheme-abc",
) -> dict:
    return {
        "typeOfRequest": type_of_request,
        "targetSchemeId": target_scheme_id,
        "Scheme": "Existing Scheme",
        "Link": "https://example.com/replacement",
        "scraped_text": "Some new page text.",
        "llm_fields": {"llm_description": "Updated description."},
    }


def _wire_db(mocker, entry_data: dict, target_status: Optional[str] = "inactive"):
    """Return (db_mock, entry_ref, target_or_new_ref)."""
    db = mocker.MagicMock()
    entry_ref = mocker.MagicMock()
    entry_snap = mocker.MagicMock()
    entry_snap.exists = True
    entry_snap.to_dict.return_value = entry_data
    entry_ref.get.return_value = entry_snap

    target_or_new_ref = mocker.MagicMock()
    target_or_new_ref.id = entry_data.get("targetSchemeId") or "scheme-new"

    target_snap = mocker.MagicMock()
    target_snap.exists = target_status is not None
    target_snap.to_dict.return_value = (
        {"status": target_status} if target_status is not None else None
    )
    target_or_new_ref.get.return_value = target_snap

    def collection(name):
        col = mocker.MagicMock()
        if name == "schemeEntries":
            col.document.return_value = entry_ref
        elif name == "schemes":
            col.document.return_value = target_or_new_ref
        return col

    db.collection.side_effect = collection
    mocker.patch(
        "new_scheme.approval_handler.firestore.client", return_value=db
    )
    return db, entry_ref, target_or_new_ref


def _mock_slack(mocker):
    slack = mocker.MagicMock()
    slack.users_info.return_value = {
        "ok": True,
        "user": {"profile": {"email": "rev@example.com"}},
    }
    return slack


def test_update_approval_patches_target_scheme(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    db, entry_ref, target_ref = _wire_db(mocker, entry_data)
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={
            "original_data": {"scraped_text": "Some new page text."},
            "llm_fields": {},
        },
    )
    slack = _mock_slack(mocker)

    mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    target_ref.update.assert_called_once()
    patch = target_ref.update.call_args.args[0]
    assert patch["link"] == "https://example.com/replacement"
    assert patch["scheme"] == "Existing Scheme"
    assert patch["status"] == "active"
    assert patch["link_check_status_code"] == 200
    assert "last_link_check" in patch
    assert "last_scraped_update" in patch
    assert "last_llm_processed_update" in patch
    assert patch["approved_by"] == "rev@example.com"
    assert patch["source_entry_id"] == "entry-1"

    # Must not have created a new doc
    target_ref.set.assert_not_called()


def test_update_approval_writes_update_flavored_slack(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    _wire_db(mocker, entry_data)
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={"original_data": {"scraped_text": ""}, "llm_fields": {}},
    )

    update_msg_builder = mocker.patch.object(
        mod, "build_scheme_update_approved_message", return_value={"blocks": []}
    )
    new_msg_builder = mocker.patch.object(
        mod, "build_new_scheme_approved_message", return_value={"blocks": []}
    )
    slack = _mock_slack(mocker)

    mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    update_msg_builder.assert_called_once()
    new_msg_builder.assert_not_called()
    kwargs = update_msg_builder.call_args.kwargs
    assert kwargs["target_scheme_id"] == "scheme-abc"
    assert kwargs["new_url"] == "https://example.com/replacement"


def test_update_approval_persists_resulting_id_on_entry(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    db, entry_ref, target_ref = _wire_db(mocker, entry_data)
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={"original_data": {"scraped_text": ""}, "llm_fields": {}},
    )
    slack = _mock_slack(mocker)

    mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    # entry_ref.update called once to write approval status
    entry_ref.update.assert_called_once()
    entry_patch = entry_ref.update.call_args.args[0]
    assert entry_patch["approved_scheme_id"] == "scheme-abc"
    assert entry_patch["Status"] == "approved"


def test_new_approval_still_creates_doc(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict(type_of_request="new", target_scheme_id=None)
    db, entry_ref, new_doc_ref = _wire_db(mocker, entry_data)
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={"original_data": {"scraped_text": ""}, "llm_fields": {}},
    )
    slack = _mock_slack(mocker)

    mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    new_doc_ref.set.assert_called_once()
    new_doc_ref.update.assert_not_called()


def test_update_rejection_uses_update_flavored_message(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    db, entry_ref, target_ref = _wire_db(mocker, entry_data)

    update_reject_builder = mocker.patch.object(
        mod, "build_scheme_update_rejected_message", return_value={"blocks": []}
    )
    new_reject_builder = mocker.patch.object(
        mod, "build_new_scheme_rejected_message", return_value={"blocks": []}
    )
    slack = mocker.MagicMock()

    mod.handle_new_scheme_rejection(
        slack, "entry-1", "C1", "1.0", "U123", reason="bad fit"
    )

    # Target scheme doc untouched
    target_ref.update.assert_not_called()
    target_ref.set.assert_not_called()

    # Entry marked rejected
    entry_ref.update.assert_called_once()
    assert entry_ref.update.call_args.args[0]["Status"] == "rejected"

    update_reject_builder.assert_called_once()
    new_reject_builder.assert_not_called()
    kwargs = update_reject_builder.call_args.kwargs
    assert kwargs["target_scheme_id"] == "scheme-abc"
    assert kwargs["reason"] == "bad fit"


def test_new_rejection_uses_new_flavored_message(mocker):
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict(type_of_request="new", target_scheme_id=None)
    _wire_db(mocker, entry_data)

    update_reject_builder = mocker.patch.object(
        mod, "build_scheme_update_rejected_message", return_value={"blocks": []}
    )
    new_reject_builder = mocker.patch.object(
        mod, "build_new_scheme_rejected_message", return_value={"blocks": []}
    )
    slack = mocker.MagicMock()

    mod.handle_new_scheme_rejection(
        slack, "entry-1", "C1", "1.0", "U123", reason=None
    )

    new_reject_builder.assert_called_once()
    update_reject_builder.assert_not_called()


def test_update_approval_warns_when_target_status_active(mocker, caplog):
    """Approving update-in-place against an active target should log a warning."""
    import logging

    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    _wire_db(mocker, entry_data, target_status="active")
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={"original_data": {"scraped_text": ""}, "llm_fields": {}},
    )
    slack = _mock_slack(mocker)

    warnings: list[str] = []

    def _capture_warning(msg, *args, **kwargs):
        warnings.append(str(msg))

    mocker.patch.object(mod.logger, "warning", side_effect=_capture_warning)

    with caplog.at_level(logging.WARNING):
        mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    assert any(
        "scheme-abc" in w and "'active'" in w for w in warnings
    ), f"expected active-status warning; got: {warnings}"


def test_update_approval_no_warning_when_target_inactive(mocker):
    """Approving update-in-place against inactive target should not warn about status."""
    from new_scheme import approval_handler as mod

    entry_data = _entry_dict()
    _wire_db(mocker, entry_data, target_status="inactive")
    mocker.patch.object(
        mod,
        "get_processed_data_from_entry",
        return_value={"original_data": {"scraped_text": ""}, "llm_fields": {}},
    )
    slack = _mock_slack(mocker)

    warnings: list[str] = []

    def _capture_warning(msg, *args, **kwargs):
        warnings.append(str(msg))

    mocker.patch.object(mod.logger, "warning", side_effect=_capture_warning)

    mod.handle_new_scheme_approval(slack, _approval_event(), "entry-1")

    assert not any("current status" in w for w in warnings)
