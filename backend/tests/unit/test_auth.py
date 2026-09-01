"""Unit tests for Firebase authentication."""

from types import SimpleNamespace

from utils.auth import verify_auth_token


def test_valid_token_initializes_firebase_before_verification(mocker):
    events = []
    mocker.patch(
        "utils.auth.FirebaseManager",
        side_effect=lambda: events.append("initialize"),
    )
    mocker.patch(
        "utils.auth.auth.verify_id_token",
        side_effect=lambda token: events.append(("verify", token)) or {"uid": "user-123"},
    )
    request = SimpleNamespace(headers={"Authorization": "Bearer valid-token"})

    result = verify_auth_token(request)

    assert result == (True, "user-123")
    assert events == ["initialize", ("verify", "valid-token")]


def test_missing_authorization_header_does_not_initialize_firebase(mocker):
    initialize = mocker.patch("utils.auth.FirebaseManager")
    verify = mocker.patch("utils.auth.auth.verify_id_token")
    request = SimpleNamespace(headers={})

    result = verify_auth_token(request)

    assert result == (False, "No valid authorization header")
    initialize.assert_not_called()
    verify.assert_not_called()


def test_invalid_token_keeps_verification_failure_response(mocker):
    initialize = mocker.patch("utils.auth.FirebaseManager")
    verify = mocker.patch(
        "utils.auth.auth.verify_id_token",
        side_effect=ValueError("invalid token"),
    )
    request = SimpleNamespace(headers={"Authorization": "Bearer invalid-token"})

    result = verify_auth_token(request)

    assert result == (False, "Token verification failed")
    initialize.assert_called_once_with()
    verify.assert_called_once_with("invalid-token")
