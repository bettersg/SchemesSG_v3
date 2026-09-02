"""Cross-endpoint contracts for public scheme discovery handlers."""

import json

import pytest
from agent.handler import agent_chat_message
from schemes.catalog import catalog
from schemes.schemes import schemes


DISCOVERY_ENDPOINTS = [
    pytest.param(catalog, "GET", {}, "/", id="catalog"),
    pytest.param(schemes, "GET", {}, "/scheme-1", id="scheme-detail"),
    pytest.param(
        agent_chat_message,
        "POST",
        {"message": "What help is available?"},
        "/",
        id="agent-stream",
    ),
]

DISCOVERY_PREFLIGHT_ENDPOINTS = [
    pytest.param(catalog, "/", id="catalog"),
    pytest.param(schemes, "/scheme-1", id="scheme-detail"),
    pytest.param(agent_chat_message, "/", id="agent-stream"),
]


@pytest.mark.parametrize("handler,method,body,path", DISCOVERY_ENDPOINTS)
def test_discovery_endpoints_require_authentication(
    handler, method, body, path, mock_request
):
    request = mock_request(
        method=method,
        json_data=body,
        headers={"Origin": "https://schemes.sg"},
    )
    request.path = path

    response = handler(request)

    assert response.status_code == 401
    assert json.loads(response.get_data(as_text=True)) == {
        "error": "Authentication failed: No valid authorization header"
    }
    assert response.content_type == "application/json"
    assert response.headers["Access-Control-Allow-Origin"] == "https://schemes.sg"


@pytest.mark.parametrize("handler,path", DISCOVERY_PREFLIGHT_ENDPOINTS)
@pytest.mark.parametrize(
    ("origin", "expected_status", "expected_allow_origin"),
    [
        ("https://schemes.sg", 204, "https://schemes.sg"),
        ("https://untrusted.example", 403, None),
    ],
)
def test_discovery_preflight_enforces_allowed_origins(
    handler,
    path,
    origin,
    expected_status,
    expected_allow_origin,
    mock_request,
):
    request = mock_request(method="OPTIONS", headers={"Origin": origin})
    request.path = path

    response = handler(request)

    assert response.status_code == expected_status
    assert response.headers.get("Access-Control-Allow-Origin") == expected_allow_origin
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type, Authorization"
    assert response.headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
