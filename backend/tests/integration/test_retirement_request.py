"""Integration contracts for retirement request validation and persistence."""

import json

import pytest


def _load_update_scheme(mocker, manager):
    from update_scheme import update_scheme as module

    mocker.patch.object(module, "create_firebase_manager", return_value=manager)
    mocker.patch.object(module, "is_local_dev", return_value=False)
    return module.update_scheme


def _request_data(**overrides):
    return {
        "typeOfRequest": "retire",
        "targetSchemeId": "duplicate",
        "retiredReason": "Duplicate of canonical scheme",
        **overrides,
    }


def _response_body(response):
    return json.loads(response.get_data())


def test_retirement_request_requires_target(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(mock_request(method="POST", json_data=_request_data(targetSchemeId=None)))

    assert response.status_code == 400
    assert "targetSchemeId" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_retirement_request_rejects_unknown_target(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(mock_request(method="POST", json_data=_request_data()))

    assert response.status_code == 400
    assert "not found" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_retirement_request_requires_reason(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.seed("schemes", "duplicate", {"status": "active"})
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(mock_request(method="POST", json_data=_request_data(retiredReason=" ")))

    assert response.status_code == 400
    assert "retiredReason" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


@pytest.mark.parametrize("merged_into", ["", "  ", 123])
def test_retirement_request_rejects_invalid_merge_target_value(
    merged_into,
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.seed("schemes", "duplicate", {"status": "active"})
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data=_request_data(mergedInto=merged_into),
        )
    )

    assert response.status_code == 400
    assert "mergedInto" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_retirement_request_rejects_self_merge(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.seed("schemes", "duplicate", {"status": "active"})
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data=_request_data(mergedInto="duplicate"),
        )
    )

    assert response.status_code == 400
    assert "itself" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


@pytest.mark.parametrize("merge_status", [None, "retired"])
def test_retirement_request_requires_live_merge_target(
    merge_status,
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.seed("schemes", "duplicate", {"status": "active"})
    if merge_status is not None:
        fake_firestore.seed("schemes", "canonical", {"status": merge_status})
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data=_request_data(mergedInto="canonical"),
        )
    )

    assert response.status_code == 400
    assert "must exist and must not be retired" in _response_body(response)["message"]
    assert fake_firestore.list_documents("schemeEntries") == {}


def test_retirement_request_persists_audit_fields(
    mock_request,
    mock_https_response,
    mock_auth,
    mocker,
    fake_firebase_manager,
    fake_firestore,
):
    fake_firestore.seed("schemes", "duplicate", {"status": "active"})
    fake_firestore.seed("schemes", "canonical", {"status": "active"})
    update_scheme = _load_update_scheme(mocker, fake_firebase_manager)

    response = update_scheme(
        mock_request(
            method="POST",
            json_data=_request_data(
                retiredReason="  Duplicate of canonical scheme  ",
                mergedInto="canonical",
                userEmail="triage@example.com",
            ),
        )
    )

    assert response.status_code == 200
    body = _response_body(response)
    stored = fake_firestore.get_document("schemeEntries", body["docId"])
    assert stored["targetSchemeId"] == "duplicate"
    assert stored["retiredReason"] == "Duplicate of canonical scheme"
    assert stored["mergedInto"] == "canonical"
    assert stored["userEmail"] == "triage@example.com"
