import json
import sys
import types


def _install_trafilatura_stub():
    trafilatura = types.ModuleType("trafilatura")
    trafilatura.settings = types.ModuleType("trafilatura.settings")

    class Config:
        def set(self, *_args):
            pass

    trafilatura.settings.use_config = lambda: Config()
    sys.modules.setdefault("trafilatura", trafilatura)
    sys.modules.setdefault("trafilatura.settings", trafilatura.settings)


def _import_agent_handler():
    _install_trafilatura_stub()
    from agent.event_type import AgentStreamEventType
    from agent.handler import agent_chat_message

    return AgentStreamEventType, agent_chat_message


def test_agent_draft_email_response_removes_stray_tamil_character(mock_request, mock_auth, mocker):
    AgentStreamEventType, agent_chat_message = _import_agent_handler()

    mocker.patch("agent.handler.stream_chat_events_sync").return_value = iter(
        [
            {
                "type": AgentStreamEventType.TEXT,
                "data": {
                    "text": "Subject: Dementia caregiver respite support enquiry அ\n\nDear Sir/Madam,\n",
                },
            },
            {"type": AgentStreamEventType.DONE, "data": {}},
        ]
    )

    request = mock_request(
        method="POST",
        json_data={
            "message": "Draft an email asking about respite care for a dementia caregiver.",
            "sessionID": "issue-322",
            "stream": False,
        },
    )

    response = agent_chat_message(request)
    payload = json.loads(response.get_data())

    assert response.status_code == 200
    assert "அ" not in payload["message"]
    assert "Subject: Dementia caregiver respite support enquiry" in payload["message"]


def test_agent_streaming_draft_email_response_removes_stray_tamil_character(mock_request, mock_auth, mocker):
    AgentStreamEventType, agent_chat_message = _import_agent_handler()

    mocker.patch("agent.handler.stream_chat_events_sync").return_value = iter(
        [
            {
                "type": AgentStreamEventType.TEXT,
                "data": {
                    "text": "Subject: Dementia caregiver respite support enquiry அ\n\nDear Sir/Madam,\n",
                },
            },
            {"type": AgentStreamEventType.DONE, "data": {}},
        ]
    )

    request = mock_request(
        method="POST",
        json_data={
            "message": "Draft an email asking about respite care for a dementia caregiver.",
            "sessionID": "issue-322",
            "stream": True,
        },
    )

    response = agent_chat_message(request)
    body = "".join(response.response)

    assert response.status_code == 200
    assert "அ" not in body
    assert "Subject: Dementia caregiver respite support enquiry" in body


def test_agent_draft_email_response_keeps_tamil_when_user_writes_tamil(mock_request, mock_auth, mocker):
    AgentStreamEventType, agent_chat_message = _import_agent_handler()

    mocker.patch("agent.handler.stream_chat_events_sync").return_value = iter(
        [
            {
                "type": AgentStreamEventType.TEXT,
                "data": {
                    "text": "தலைப்பு: பராமரிப்பாளர் ஓய்வு ஆதரவு விசாரணை\n\nஅன்புள்ள ஐயா/அம்மா,\n",
                },
            },
            {"type": AgentStreamEventType.DONE, "data": {}},
        ]
    )

    request = mock_request(
        method="POST",
        json_data={
            "message": "மறதி நோயாளியை பார்த்துக் கொள்ளும் பராமரிப்பாளருக்கான ஓய்வு பராமரிப்பு பற்றி மின்னஞ்சல் வரைவு செய்யுங்கள்.",
            "sessionID": "issue-322-tamil",
            "stream": False,
        },
    )

    response = agent_chat_message(request)
    payload = json.loads(response.get_data())

    assert response.status_code == 200
    assert "தலைப்பு" in payload["message"]
    assert "அன்புள்ள" in payload["message"]
