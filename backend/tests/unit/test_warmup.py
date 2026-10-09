"""Warmup authentication, bounded waits, and nonfatal failure reporting."""

from types import SimpleNamespace

import pytest
from flask import Flask, request
from utils import endpoints


@pytest.fixture
def transport(mocker, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("FB_PROJECT_ID", "schemessg-v3-dev")
    monkeypatch.setenv("FB_API_KEY", "test-key")
    state = {"initialized": False}

    def initialize():
        state["initialized"] = True

    def sign(*args, **kwargs):
        assert state["initialized"], "Firebase Admin must initialize before signing"
        return b"test-custom-token"

    manager = mocker.patch("utils.endpoints.FirebaseManager", create=True, side_effect=initialize)
    signer = mocker.patch("utils.endpoints.auth.create_custom_token", side_effect=sign)
    exchange = mocker.patch("utils.endpoints.requests.post", return_value=SimpleNamespace(
        status_code=200, json=lambda: {"idToken": "test-id-token"},
    ))
    ping = mocker.patch("utils.endpoints.requests.request", return_value=SimpleNamespace(status_code=200))
    return SimpleNamespace(manager=manager, signer=signer, exchange=exchange, ping=ping)


def invoke_schedule():
    app = Flask(__name__)
    with app.test_request_context("/", method="POST"):
        return endpoints.keep_endpoints_warm(request)


def test_warmup_initializes_admin_before_authenticated_ping(transport):
    payload = {"is_warmup": True}
    assert endpoints.make_warmup_request("https://example.invalid", "POST", payload)
    transport.manager.assert_called_once()
    transport.signer.assert_called_once_with("warmup-user")
    assert transport.exchange.call_args.kwargs["timeout"] == 10
    transport.ping.assert_called_once_with(
        method="POST", url="https://example.invalid", json=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer test-id-token"},
        timeout=30,
    )


def test_initialization_failure_does_not_sign_or_send_requests(transport):
    transport.manager.side_effect = RuntimeError("initialization failed")
    assert not endpoints.make_warmup_request("https://example.invalid")
    transport.signer.assert_not_called()
    transport.exchange.assert_not_called()
    transport.ping.assert_not_called()


@pytest.mark.parametrize("failure", ["timeout", "rejected"])
def test_token_exchange_failure_does_not_ping(transport, failure):
    if failure == "timeout":
        transport.exchange.side_effect = endpoints.requests.exceptions.Timeout("token exchange timed out")
    else:
        transport.exchange.return_value = SimpleNamespace(status_code=403)
    assert not endpoints.make_warmup_request("https://example.invalid")
    assert transport.exchange.call_args.kwargs["timeout"] == 10
    transport.ping.assert_not_called()


def test_successful_schedule_preserves_all_seven_warmup_targets(transport):
    assert invoke_schedule().status_code == 200
    assert transport.ping.call_count == 7
    for call in transport.ping.call_args_list:
        if call.kwargs["method"] == "GET":
            assert "is_warmup=true" in call.kwargs["url"]
        else:
            assert call.kwargs["json"]["is_warmup"] is True


@pytest.mark.parametrize("results", [
    [False] * 7,
    [True, True, False, True, True, True, True],
])
def test_failed_schedule_attempts_every_target_logs_names_and_returns_200(mocker, results):
    ping = mocker.patch("utils.endpoints.make_warmup_request", side_effect=results)
    warning = mocker.patch("utils.endpoints.logger.warning")
    response = invoke_schedule()
    assert ping.call_count == 7
    assert response.status_code == 200
    warning.assert_called_once()
    message = warning.call_args.args[0]
    assert "agent_chat_message" in message
    assert f"{sum(results)}/7" in message


def test_authentication_timeout_does_not_prevent_later_targets(transport):
    success = SimpleNamespace(status_code=200, json=lambda: {"idToken": "test-id-token"})
    transport.exchange.side_effect = [endpoints.requests.exceptions.Timeout("timeout")] + [success] * 6
    assert invoke_schedule().status_code == 200
    assert transport.exchange.call_count == 7
    assert transport.ping.call_count == 6


def test_unexpected_scheduler_failure_is_logged_without_failing_job(mocker):
    mocker.patch("utils.endpoints.get_endpoint_url", side_effect=RuntimeError("invalid configuration"))
    error = mocker.patch("utils.endpoints.logger.exception")
    assert invoke_schedule().status_code == 200
    error.assert_called_once()
