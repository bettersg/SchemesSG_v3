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
    mocker.patch.object(mod, "get_firestore_client", return_value=MagicMock())
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


NEW_DATA = {"Scheme": "New Scheme", "Link": "https://example.com/new", "typeOfRequest": "new"}


def _response(status, body=None):
    import requests

    resp = MagicMock(status_code=status)
    resp.json.return_value = body or {}
    if status >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status} Server Error", response=resp)
    return resp


def _patch_retry(mocker, *, entry=None):
    """Patch the trigger for retry tests and return (mod, post_mock, entry_ref, slack_client)."""
    mod, post_mock = _patch_common(mocker)
    mocker.patch.object(mod, "check_duplicate_scheme", return_value=None)
    mocker.patch("time.sleep")
    entry_ref = MagicMock()
    entry_ref.get.return_value.to_dict.return_value = entry or {}
    mod.get_firestore_client.return_value.collection.return_value.document.return_value = entry_ref
    slack_client = MagicMock()
    mocker.patch.object(mod, "get_slack_client", return_value=slack_client)
    mocker.patch.object(mod, "get_slack_channel", return_value="C123")
    return mod, post_mock, entry_ref, slack_client


def _failed_updates(entry_ref):
    return [c.args[0] for c in entry_ref.update.call_args_list if c.args[0].get("pipeline_status") == "failed"]


def test_transient_503_is_retried_and_entry_not_failed(mocker):
    mod, post_mock, entry_ref, slack_client = _patch_retry(mocker)
    post_mock.side_effect = [_response(503), _response(200, {"success": True})]

    mod.process_new_scheme_entry("entry-503", NEW_DATA)

    assert post_mock.call_count == 2
    assert _failed_updates(entry_ref) == []
    slack_client.chat_postMessage.assert_not_called()


def test_429_and_connection_error_are_retried(mocker):
    import requests

    mod, post_mock, entry_ref, _ = _patch_retry(mocker)
    post_mock.side_effect = [
        _response(429),
        requests.exceptions.ConnectionError("reset"),
        _response(200, {"success": True}),
    ]

    mod.process_new_scheme_entry("entry-429", NEW_DATA)

    assert post_mock.call_count == 3
    assert _failed_updates(entry_ref) == []


def test_persistent_503_marks_failed_and_alerts_slack(mocker):
    mod, post_mock, entry_ref, slack_client = _patch_retry(mocker)
    post_mock.return_value = _response(503)

    mod.process_new_scheme_entry("entry-dead", NEW_DATA)

    assert post_mock.call_count == mod.PROCESSOR_MAX_ATTEMPTS
    failed = _failed_updates(entry_ref)
    assert len(failed) == 1
    assert "503" in failed[0]["pipeline_error"]
    slack_client.chat_postMessage.assert_called_once()
    alert = slack_client.chat_postMessage.call_args.kwargs
    assert alert["channel"] == "C123"
    assert "entry-dead" in alert["text"]


def test_slack_alert_failure_does_not_block_failed_status(mocker):
    mod, post_mock, entry_ref, slack_client = _patch_retry(mocker)
    post_mock.return_value = _response(503)
    slack_client.chat_postMessage.side_effect = RuntimeError("slack down")

    mod.process_new_scheme_entry("entry-dead", NEW_DATA)

    assert len(_failed_updates(entry_ref)) == 1


def test_503_after_review_card_posted_is_not_retried(mocker):
    """The processor posts the review card last; retrying after that would post a second card."""
    mod, post_mock, entry_ref, _ = _patch_retry(mocker, entry={"slack_message_ts": "171.1"})
    post_mock.side_effect = [_response(503), _response(200, {"success": True})]

    mod.process_new_scheme_entry("entry-carded", NEW_DATA)

    assert post_mock.call_count == 1
    assert _failed_updates(entry_ref) == []


def test_timeout_is_not_retried(mocker):
    """The processor may still be running after a client timeout, so a retry could process twice."""
    import requests

    mod, post_mock, entry_ref, slack_client = _patch_retry(mocker)
    post_mock.side_effect = requests.exceptions.Timeout("slow")

    mod.process_new_scheme_entry("entry-slow", NEW_DATA)

    assert post_mock.call_count == 1
    assert len(_failed_updates(entry_ref)) == 1
    slack_client.chat_postMessage.assert_called_once()


def test_client_error_is_not_retried(mocker):
    mod, post_mock, entry_ref, _ = _patch_retry(mocker)
    post_mock.return_value = _response(400)

    mod.process_new_scheme_entry("entry-bad", NEW_DATA)

    assert post_mock.call_count == 1
    assert len(_failed_updates(entry_ref)) == 1


def test_client_timeout_exceeds_processor_timeout(mocker):
    """Cloud Run's own 300s timeout should answer before the client gives up."""
    mod, post_mock, _, _ = _patch_retry(mocker)
    post_mock.return_value = _response(200, {"success": True})

    mod.process_new_scheme_entry("entry-ok", NEW_DATA)

    assert post_mock.call_args.kwargs["timeout"] > 300


def test_processor_reported_failure_alerts_slack(mocker):
    mod, post_mock, _, slack_client = _patch_retry(mocker)
    post_mock.return_value = _response(200, {"success": False, "error": "LLM down"})

    mod.process_new_scheme_entry("entry-llm", NEW_DATA)

    assert post_mock.call_count == 1
    assert "LLM down" in slack_client.chat_postMessage.call_args.kwargs["text"]


def test_503_is_not_retried_without_time_for_another_attempt(mocker):
    """A slow 503 leaves too little of the function's 540s for another full attempt."""
    mod, post_mock, entry_ref, _ = _patch_retry(mocker)
    mocker.patch.object(mod.time, "monotonic", side_effect=[0, 250])
    post_mock.side_effect = [_response(503), _response(200, {"success": True})]

    mod.process_new_scheme_entry("entry-slow-503", NEW_DATA)

    assert post_mock.call_count == 1
    assert len(_failed_updates(entry_ref)) == 1


def test_connection_reset_after_processor_started_is_not_retried(mocker):
    """`requests` raises ConnectionError for a reset after the POST was sent; the processor keeps running."""
    import requests

    mod, post_mock, entry_ref, slack_client = _patch_retry(
        mocker, entry={"pipeline_status": "processing", "pipeline_started_at": "2999-01-01T00:00:00+00:00"}
    )
    post_mock.side_effect = [
        requests.exceptions.ConnectionError("Connection aborted: RemoteDisconnected"),
        _response(200, {"success": True}),
    ]

    mod.process_new_scheme_entry("entry-reset", NEW_DATA)

    assert post_mock.call_count == 1
    assert _failed_updates(entry_ref) == []
    alert = slack_client.chat_postMessage.call_args.kwargs["text"]
    assert "entry-reset" in alert
    assert "not retried" in alert


def test_connection_error_after_an_earlier_attempt_started_is_retried(mocker):
    """A `pipeline_started_at` left by an earlier attempt does not mean this attempt reached the processor."""
    import requests

    mod, post_mock, entry_ref, _ = _patch_retry(
        mocker, entry={"pipeline_status": "processing", "pipeline_started_at": "2000-01-01T00:00:00+00:00"}
    )
    post_mock.side_effect = [requests.exceptions.ConnectionError("refused"), _response(200, {"success": True})]

    mod.process_new_scheme_entry("entry-refused", NEW_DATA)

    assert post_mock.call_count == 2
    assert _failed_updates(entry_ref) == []


def test_503_after_review_card_still_warns_about_shared_link(mocker, update_data):
    mod, post_mock, _, slack_client = _patch_retry(
        mocker, entry={"slack_channel": "C9", "slack_message_ts": "171.1", "targetSchemeId": "scheme-abc"}
    )
    mocker.patch.object(
        mod,
        "check_duplicate_scheme",
        return_value={"doc_id": "scheme-other", "scheme": "Other", "link": "https://example.com/foo"},
    )
    post_mock.return_value = _response(503)

    mod.process_new_scheme_entry("entry-shared", update_data)

    assert post_mock.call_count == 1
    warning = slack_client.chat_postMessage.call_args.kwargs
    assert warning["thread_ts"] == "171.1"
    assert "scheme-other" in warning["text"]
