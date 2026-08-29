"""Handler-level integration tests for the current agent chat endpoint."""

import json

from agent.event_type import AgentStreamEventType
from agent.handler import agent_chat_message


def response_json(response):
    return json.loads(response.get_data(as_text=True))


def test_chat_warmup_request(mock_request, mock_https_response, mock_auth):
    request = mock_request(method="POST", json_data={"is_warmup": True})

    response = agent_chat_message(request)

    assert response.status_code == 200
    assert response_json(response)["message"] == "Warmup request successful"


def test_chat_invalid_method(mock_request, mock_https_response, mock_auth):
    response = agent_chat_message(mock_request(method="GET"))

    assert response.status_code == 405
    assert response_json(response)["error"] == "Invalid request method; only POST is supported"


def test_chat_missing_message(mock_request, mock_https_response, mock_auth):
    request = mock_request(method="POST", json_data={"sessionID": "test-session"})

    response = agent_chat_message(request)

    assert response.status_code == 400
    assert response_json(response)["error"] == "'message' is required"


def test_chat_authentication_failure(mock_request, mock_https_response, mocker):
    mocker.patch("agent.handler.verify_auth_token", return_value=(False, "Invalid token"))
    request = mock_request(method="POST", json_data={"message": "test"})

    response = agent_chat_message(request)

    assert response.status_code == 401
    assert response_json(response)["error"] == "Authentication failed: Invalid token"


def test_chat_invalid_json(mock_request, mock_https_response, mock_auth, mocker):
    request = mock_request(method="POST")
    mocker.patch.object(request, "get_json", side_effect=ValueError("Invalid JSON"))

    response = agent_chat_message(request)

    assert response.status_code == 400
    assert response_json(response)["error"] == "Invalid request body"


def test_chat_generates_session_id(mock_request, mock_https_response, mock_auth, mocker):
    mocker.patch("agent.handler.uuid1", return_value="generated-session")
    mocker.patch("agent.handler.stream_chat_events_sync", return_value=iter(()))
    request = mock_request(method="POST", json_data={"message": "test", "stream": False})

    response = agent_chat_message(request)

    assert response.status_code == 200
    assert response_json(response)["sessionID"] == "generated-session"


def test_chat_successful_response(mock_request, mock_https_response, mock_auth, mocker):
    mocker.patch(
        "agent.handler.stream_chat_events_sync",
        return_value=iter(
            [
                {"type": AgentStreamEventType.TEXT, "data": {"text": "Test "}},
                {"type": AgentStreamEventType.TEXT, "data": {"text": "response"}},
            ]
        ),
    )
    request = mock_request(
        method="POST",
        json_data={"message": "test", "sessionID": "test-session", "stream": False},
    )

    response = agent_chat_message(request)

    assert response.status_code == 200
    body = response_json(response)
    assert body["response"] is True
    assert body["message"] == "Test response"


def test_chat_streaming_response(mock_request, mock_https_response, mock_auth, mocker):
    mocker.patch(
        "agent.handler.stream_chat_events_sync",
        return_value=iter([{"type": AgentStreamEventType.TEXT, "data": {"text": "Hello"}}]),
    )
    request = mock_request(
        method="POST",
        json_data={"message": "test", "sessionID": "test-session", "stream": True},
    )

    response = agent_chat_message(request)

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"


def test_chat_runtime_error(mock_request, mock_https_response, mock_auth, mocker):
    mocker.patch(
        "agent.handler.stream_chat_events_sync",
        side_effect=RuntimeError("Agent error"),
    )
    request = mock_request(
        method="POST",
        json_data={"message": "test", "sessionID": "test-session", "stream": False},
    )

    response = agent_chat_message(request)

    assert response.status_code == 500
    assert response_json(response)["error"] == "Internal server error"


def test_chat_options_request(mock_request, mock_https_response, mocker):
    expected = mock_https_response("", status=204)
    preflight = mocker.patch("agent.handler.handle_cors_preflight", return_value=expected)
    request = mock_request(method="OPTIONS")

    response = agent_chat_message(request)

    assert response is expected
    preflight.assert_called_once_with(request)
