"""Contracts for how the scheme-entry trigger treats a link another scheme already has."""

import pytest
from new_scheme import trigger_new_scheme_pipeline as trigger
from new_scheme import url_utils


SHARED = "https://www.example.org/services/youth-outreach/"


@pytest.fixture
def processor(mocker, fake_firestore, fake_slack_client):
    fake_firestore.seed("schemes", "owner", {"scheme": "Youth Outreach", "link": SHARED, "status": "active"})
    fake_firestore.seed("schemes", "target", {"scheme": "Online Outreach", "link": "https://old.example.org/online"})
    for module in (trigger, url_utils):
        mocker.patch.object(module, "get_firestore_client", return_value=fake_firestore)
    mocker.patch.object(trigger, "get_slack_client", return_value=fake_slack_client)
    mocker.patch.object(trigger, "get_slack_channel", return_value="C-review")

    def process(url, json, **_):
        # The scheme-processor scrapes, posts the review card and records where it went.
        fake_firestore.collection("schemeEntries").document(json["doc_id"]).update(
            {"pipeline_status": "completed", "slack_channel": "C-review", "slack_message_ts": "card-1"}
        )
        response = mocker.Mock()
        response.json.return_value = {"success": True, "slack_ts": "card-1"}
        return response

    return mocker.patch.object(trigger.requests, "post", side_effect=process)


def _submit(fake_firestore, entry_id, **entry):
    fake_firestore.seed("schemeEntries", entry_id, entry)
    trigger.process_new_scheme_entry(entry_id, entry)
    return fake_firestore.get_document("schemeEntries", entry_id)


def test_update_to_another_schemes_link_still_gets_a_review_card_with_a_warning(
    processor, fake_firestore, fake_slack_client
):
    stored = _submit(
        fake_firestore, "entry-update", typeOfRequest="update", targetSchemeId="target", Scheme="Online", Link=SHARED
    )

    processor.assert_called_once()
    assert stored["pipeline_status"] == "completed"
    [warning] = fake_slack_client.posted_messages
    assert (warning["channel"], warning["thread_ts"], warning["reply_broadcast"]) == ("C-review", "card-1", True)
    assert "*Youth Outreach* (`owner`)" in warning["text"]
    assert "retire `target` with Merged into `owner`" in warning["text"]


def test_new_scheme_with_an_existing_link_is_still_blocked(processor, fake_firestore, fake_slack_client):
    stored = _submit(fake_firestore, "entry-new", typeOfRequest="new", Scheme="Youth Outreach copy", Link=SHARED)

    processor.assert_not_called()
    assert (stored["pipeline_status"], stored["duplicate_scheme_id"]) == ("duplicate", "owner")
    assert len(fake_slack_client.posted_messages) == 1
