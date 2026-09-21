"""Public Slack interaction contracts for scheme approval and rejection."""

import json

from new_scheme import approval_handler
from slack_integration import slack as slack_module


def _request(mock_request, event):
    return mock_request(
        method="POST",
        json_data=event,
        headers={"Content-Type": "application/json"},
    )


def _approval_event(entry_id: str) -> dict:
    return {
        "type": "view_submission",
        "user": {"id": "U-reviewer"},
        "view": {
            "callback_id": "new_scheme_approval_submit",
            "private_metadata": json.dumps({"doc_id": entry_id, "channel": "C-review", "message_ts": "1.0"}),
            "state": {
                "values": {
                    "scheme_name_block": {"scheme_name": {"value": "New Support"}},
                    "scheme_url_block": {"scheme_url": {"value": "https://example.gov.sg/support"}},
                    "agency_block": {"agency": {"value": "Example Agency"}},
                    "llm_description_block": {"llm_description": {"value": "Support for residents."}},
                }
            },
        },
    }


def _block_action(action_id: str, entry_id: str) -> dict:
    return {
        "type": "block_actions",
        "user": {"id": "U-reviewer"},
        "trigger_id": "trigger-1",
        "container": {"channel_id": "C-review", "message_ts": "1.0"},
        "actions": [{"action_id": action_id, "value": entry_id}],
    }


def _retirement_rejection_event(metadata: str, reason: str) -> dict:
    return {
        "type": "view_submission",
        "user": {"id": "U-reviewer"},
        "view": {
            "callback_id": "scheme_retirement_rejection_submit",
            "private_metadata": metadata,
            "state": {
                "values": {"retirement_rejection_reason_block": {"retirement_rejection_reason": {"value": reason}}}
            },
        },
    }


def _wire_external_boundaries(mocker, fake_firestore, fake_slack_client):
    mocker.patch.object(slack_module, "verify_slack_signature", return_value=True)
    mocker.patch.object(slack_module, "get_slack_client", return_value=fake_slack_client)
    mocker.patch.object(approval_handler, "get_firestore_client", return_value=fake_firestore)


def test_slack_approval_creates_scheme_and_marks_entry_approved(
    mock_request,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    fake_firestore.seed(
        "schemeEntries",
        "entry-new",
        {
            "typeOfRequest": "new",
            "Scheme": "New Support",
            "Link": "https://example.gov.sg/support",
            "scraped_text": "Public page text",
            "llm_fields": {"summary": "Short summary"},
        },
    )
    _wire_external_boundaries(mocker, fake_firestore, fake_slack_client)

    response = slack_module.slack_interactive(_request(mock_request, _approval_event("entry-new")))

    assert response.status_code == 200
    assert json.loads(response.get_data()) == {"response_action": "clear"}
    entry = fake_firestore.get_document("schemeEntries", "entry-new")
    scheme = fake_firestore.get_document("schemes", entry["approved_scheme_id"])
    assert entry["Status"] == "approved"
    assert scheme["scheme"] == "New Support"
    assert scheme["link"] == "https://example.gov.sg/support"
    assert scheme["status"] == "active"
    assert scheme["approved_by"] == "reviewer@example.com"
    assert any(message.get("channel") == "C-review" for message in fake_slack_client.updated_messages)
    assert any("has been added" in message.get("text", "") for message in fake_slack_client.posted_messages)


def test_slack_rejection_marks_entry_without_changing_target_scheme(
    mock_request,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    target = {
        "scheme": "Existing Support",
        "link": "https://old.example.gov.sg/support",
        "status": "inactive",
    }
    fake_firestore.seed("schemes", "scheme-1", target)
    fake_firestore.seed(
        "schemeEntries",
        "entry-update",
        {
            "typeOfRequest": "update",
            "targetSchemeId": "scheme-1",
            "Scheme": "Existing Support",
        },
    )
    _wire_external_boundaries(mocker, fake_firestore, fake_slack_client)

    response = slack_module.slack_interactive(
        _request(mock_request, _block_action("reject_new_scheme", "entry-update"))
    )

    assert response.status_code == 200
    entry = fake_firestore.get_document("schemeEntries", "entry-update")
    assert entry["Status"] == "rejected"
    assert entry["pipeline_status"] == "rejected"
    assert entry["rejected_by"] == "U-reviewer"
    assert fake_firestore.get_document("schemes", "scheme-1") == target
    assert any(message.get("channel") == "C-review" for message in fake_slack_client.updated_messages)


def test_slack_retirement_approval_retires_scheme_and_removes_embedding(
    mock_request,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    fake_firestore.seed(
        "schemeEntries",
        "entry-retire",
        {
            "typeOfRequest": "retire",
            "targetSchemeId": "duplicate",
            "mergedInto": "canonical",
            "retiredReason": "Duplicate record",
            "Scheme": "Duplicate Support",
        },
    )
    fake_firestore.seed(
        "schemes",
        "duplicate",
        {"scheme": "Duplicate Support", "status": "inactive"},
    )
    fake_firestore.seed(
        "schemes",
        "canonical",
        {"scheme": "Canonical Support", "status": "active"},
    )
    fake_firestore.seed("schemes_embeddings", "duplicate", {"embedding": [0.1]})
    _wire_external_boundaries(mocker, fake_firestore, fake_slack_client)

    response = slack_module.slack_interactive(
        _request(
            mock_request,
            _block_action("approve_scheme_retirement", "entry-retire"),
        )
    )

    assert response.status_code == 200
    scheme = fake_firestore.get_document("schemes", "duplicate")
    entry = fake_firestore.get_document("schemeEntries", "entry-retire")
    assert scheme["status"] == "retired"
    assert scheme["merged_into"] == "canonical"
    assert scheme["retired_by"] == "reviewer@example.com"
    assert entry["Status"] == "approved"
    assert fake_firestore.get_document("schemes_embeddings", "duplicate") is None


def test_slack_retirement_rejection_records_reason(
    mock_request,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    fake_firestore.seed(
        "schemeEntries",
        "entry-retire",
        {
            "typeOfRequest": "retire",
            "targetSchemeId": "duplicate",
            "Scheme": "Duplicate Support",
        },
    )
    _wire_external_boundaries(mocker, fake_firestore, fake_slack_client)
    open_response = slack_module.slack_interactive(
        _request(
            mock_request,
            _block_action("reject_scheme_retirement", "entry-retire"),
        )
    )
    metadata = fake_slack_client.opened_views[0]["view"]["private_metadata"]
    rejection_event = _retirement_rejection_event(metadata, "Keep this scheme listed")

    rejection_response = slack_module.slack_interactive(_request(mock_request, rejection_event))

    assert open_response.status_code == 200
    assert rejection_response.status_code == 200
    assert json.loads(rejection_response.get_data()) == {"response_action": "clear"}
    entry = fake_firestore.get_document("schemeEntries", "entry-retire")
    assert entry["Status"] == "rejected"
    assert entry["rejection_reason"] == "Keep this scheme listed"


def test_slack_retirement_rejection_requires_reason(
    mock_request,
    mocker,
    fake_firestore,
    fake_slack_client,
):
    original_entry = {
        "typeOfRequest": "retire",
        "targetSchemeId": "duplicate",
        "Scheme": "Duplicate Support",
    }
    fake_firestore.seed("schemeEntries", "entry-retire", original_entry)
    _wire_external_boundaries(mocker, fake_firestore, fake_slack_client)
    metadata = json.dumps({"doc_id": "entry-retire", "channel": "C-review", "message_ts": "1.0"})

    response = slack_module.slack_interactive(_request(mock_request, _retirement_rejection_event(metadata, "  ")))

    assert response.status_code == 200
    assert json.loads(response.get_data()) == {
        "response_action": "errors",
        "errors": {"retirement_rejection_reason_block": "A rejection reason is required"},
    }
    assert fake_firestore.get_document("schemeEntries", "entry-retire") == original_entry
