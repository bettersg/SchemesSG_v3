"""Integration tests for the new-scheme pipeline trigger (update flow)."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _stub_processor_url(monkeypatch):
    monkeypatch.setenv("PROCESSOR_SERVICE_URL", "http://scheme-processor:8081")


@pytest.fixture
def update_data():
    return {
        "Scheme": "Example Scheme",
        "Link": "https://example.com/foo",
        "typeOfRequest": "update",
        "targetSchemeId": "scheme-abc",
    }


def _patch_common(mocker):
    from new_scheme import trigger_new_scheme_pipeline as mod

    post_mock = mocker.patch.object(mod.requests, "post")
    post_mock.return_value = MagicMock()
    post_mock.return_value.json.return_value = {"success": True}
    post_mock.return_value.raise_for_status = MagicMock()
    mocker.patch.object(mod, "get_identity_token", return_value="tok")
    mocker.patch.object(mod, "firestore")
    return mod, post_mock


def test_process_new_scheme_entry_update_forwards_target(mocker, update_data):
    mod, post_mock = _patch_common(mocker)
    mocker.patch.object(mod, "check_duplicate_scheme", return_value=None)

    mod.process_new_scheme_entry("entry-1", update_data)

    call = post_mock.call_args
    body = call.kwargs["json"]
    assert body["doc_id"] == "entry-1"
    assert body["type_of_request"] == "update"
    assert body["target_scheme_id"] == "scheme-abc"
    assert body["scheme_url"] == "https://example.com/foo"


def test_process_new_scheme_entry_update_excludes_target_from_dup(mocker, update_data):
    mod, _ = _patch_common(mocker)
    dup_mock = mocker.patch.object(mod, "check_duplicate_scheme", return_value=None)

    mod.process_new_scheme_entry("entry-1", update_data)

    dup_mock.assert_called_once_with("https://example.com/foo", exclude_doc_id="scheme-abc")


def test_process_new_scheme_entry_new_keeps_old_behaviour(mocker):
    mod, post_mock = _patch_common(mocker)
    dup_mock = mocker.patch.object(mod, "check_duplicate_scheme", return_value=None)

    mod.process_new_scheme_entry(
        "entry-2",
        {
            "Scheme": "New Scheme",
            "Link": "https://example.com/new",
            "typeOfRequest": "new",
        },
    )

    dup_mock.assert_called_once_with("https://example.com/new", exclude_doc_id=None)
    body = post_mock.call_args.kwargs["json"]
    assert body["type_of_request"] == "new"
    assert body["target_scheme_id"] is None


def test_process_new_scheme_entry_edit_still_skipped(mocker):
    mod, post_mock = _patch_common(mocker)

    mod.process_new_scheme_entry(
        "entry-3",
        {"Scheme": "X", "Link": "https://x", "typeOfRequest": "Edit"},
    )

    post_mock.assert_not_called()


def test_process_new_scheme_entry_update_duplicate_short_circuits(mocker, update_data):
    mod, post_mock = _patch_common(mocker)
    mocker.patch.object(
        mod,
        "check_duplicate_scheme",
        return_value={
            "doc_id": "scheme-xyz",
            "scheme": "Other",
            "link": "https://example.com/foo",
            "normalized_url": "example.com/foo",
        },
    )
    mocker.patch.object(mod, "post_duplicate_to_slack")

    mod.process_new_scheme_entry("entry-1", update_data)

    # Short-circuit: no Cloud Run call
    post_mock.assert_not_called()
