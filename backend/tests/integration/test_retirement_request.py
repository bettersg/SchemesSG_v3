"""Integration tests for retirement request validation and persistence."""

import json


def _load_update_scheme(mocker, manager):
    """Import the endpoint without constructing a real Firebase manager."""
    from update_scheme import update_scheme as module

    mocker.patch.object(module, "create_firebase_manager", return_value=manager)
    return module.update_scheme


def _target(exists=True, status="active"):
    snap = type("Snap", (), {})()
    snap.exists = exists
    snap.to_dict = lambda: {"status": status}
    return snap


def test_retirement_request_requires_reason(mock_request, mock_https_response, mock_auth, mocker):
    manager = mocker.MagicMock()
    manager.firestore_client.collection().document().get.return_value = _target()
    update_scheme = _load_update_scheme(mocker, manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data={
                "typeOfRequest": "retire",
                "targetSchemeId": "duplicate",
            },
        )
    )

    assert response.status_code == 400
    assert "retiredReason" in json.loads(response.get_data())["message"]


def test_retirement_request_persists_audit_fields(mock_request, mock_https_response, mock_auth, mocker):
    manager = mocker.MagicMock()
    target = _target()
    canonical = _target()
    manager.firestore_client.collection().document().get.side_effect = [
        target,
        canonical,
    ]
    doc_ref = mocker.MagicMock(id="entry-1")
    manager.firestore_client.collection().add.return_value = (mocker.MagicMock(), doc_ref)
    update_scheme = _load_update_scheme(mocker, manager)
    mocker.patch("update_scheme.update_scheme.is_local_dev", return_value=False)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data={
                "typeOfRequest": "retire",
                "targetSchemeId": "duplicate",
                "retiredReason": "Duplicate of canonical scheme",
                "mergedInto": "canonical",
                "userEmail": "triage@example.com",
            },
        )
    )

    assert response.status_code == 200
    persisted = manager.firestore_client.collection().add.call_args.args[0]
    assert persisted["targetSchemeId"] == "duplicate"
    assert persisted["retiredReason"] == "Duplicate of canonical scheme"
    assert persisted["mergedInto"] == "canonical"


def test_retirement_request_rejects_self_merge(mock_request, mock_https_response, mock_auth, mocker):
    manager = mocker.MagicMock()
    manager.firestore_client.collection().document().get.return_value = _target()
    update_scheme = _load_update_scheme(mocker, manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data={
                "typeOfRequest": "retire",
                "targetSchemeId": "duplicate",
                "retiredReason": "Duplicate",
                "mergedInto": "duplicate",
            },
        )
    )

    assert response.status_code == 400
    assert "itself" in json.loads(response.get_data())["message"]
