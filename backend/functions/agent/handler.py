"""Agent chat endpoint backed by the runtime streaming module.

Local URL (emulator):
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/agent_chat_message
"""

from __future__ import annotations

import json
from uuid import uuid1

from firebase_functions import https_fn, options
from utils.auth import verify_auth_token
from utils.cors_config import get_cors_headers, handle_cors_preflight
from utils.json_utils import safe_json_dumps
from utils.logging_setup import setup_logging

from .engine import stream_chat_events
from .event_type import AgentStreamEventType, StatusPhase
from .output_sanitizer import sanitize_assistant_text_for_user_scripts


logger = setup_logging()


def stream_chat_events_sync(input_text: str, session_id: str):
    for event in stream_chat_events(input_text=input_text, session_id=session_id):
        yield event


@https_fn.on_request(
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
)
def agent_chat_message(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint for runtime-based agent chat and streaming."""

    if req.method == "OPTIONS":
        return handle_cors_preflight(req)

    headers = get_cors_headers(req)

    is_valid, auth_message = verify_auth_token(req)
    if not is_valid:
        return https_fn.Response(
            response=json.dumps({"error": f"Authentication failed: {auth_message}"}),
            status=401,
            mimetype="application/json",
            headers=headers,
        )

    if req.method != "POST":
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request method; only POST is supported"}),
            status=405,
            mimetype="application/json",
            headers=headers,
        )

    try:
        data = req.get_json(silent=True) or {}
        input_text = str(data.get("message", "")).strip()
        session_id = str(data.get("sessionID", "")).strip()
        stream = bool(data.get("stream", True))
        is_warmup = bool(data.get("is_warmup", False))
    except Exception:
        return https_fn.Response(
            response=json.dumps({"error": "Invalid request body"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    if is_warmup:
        return https_fn.Response(
            response=json.dumps({"message": "Warmup request successful"}),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    if not input_text:
        return https_fn.Response(
            response=json.dumps({"error": "'message' is required"}),
            status=400,
            mimetype="application/json",
            headers=headers,
        )

    # Match schemes_search behavior: generate a sessionID for fresh requests.
    if not session_id:
        session_id = str(uuid1())

    try:
        if stream:

            def generate():
                yield f"data: {safe_json_dumps({'type': AgentStreamEventType.STATUS, 'data': {'phase': StatusPhase.SESSION_STARTED, 'sessionID': session_id, 'label': 'Session started'}})}\n\n"
                for event in stream_chat_events_sync(input_text=input_text, session_id=session_id):
                    event_type = event.get("type", "")
                    event_data = event.get("data", {})
                    if not isinstance(event_data, dict):
                        event_data = {}

                    if event_type == AgentStreamEventType.TEXT:
                        text_value = str(event_data.get("text", "") or "")
                        text_value = sanitize_assistant_text_for_user_scripts(text_value, input_text)
                        if text_value:
                            yield f"data: {safe_json_dumps({'type': AgentStreamEventType.TEXT, 'data': {'text': text_value}})}\n\n"
                        continue

                    # Forward non-text events with explicit type/data for frontend handling.
                    yield f"data: {safe_json_dumps({'type': event_type, 'data': event_data})}\n\n"

            stream_headers = {
                **headers,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }

            return https_fn.Response(
                response=generate(),
                status=200,
                mimetype="text/event-stream",
                headers=stream_headers,
            )

        assistant_text = ""
        final_schemes = []
        schemes_history = []
        search_history = []
        tool_history = []
        followups = {}
        status_history: list[dict] = []
        action_messages: list[str] = []
        action_message_labels: list[str] = []
        buffered_chunks: list[str] = []

        for event in stream_chat_events_sync(input_text=input_text, session_id=session_id):
            event_type = event.get("type", "")
            event_data = event.get("data", {})
            if not isinstance(event_data, dict):
                event_data = {}
            if event_type == AgentStreamEventType.TEXT:
                text = event_data.get("text", "")
                if isinstance(text, str) and text:
                    buffered_chunks.append(sanitize_assistant_text_for_user_scripts(text, input_text))
            elif event_type == AgentStreamEventType.STATUS:
                phase_raw = event_data.get("phase", "")
                if hasattr(phase_raw, "value"):
                    phase = str(getattr(phase_raw, "value", "") or "")
                else:
                    phase = str(phase_raw or "")

                label_raw = event_data.get("label", "") or event_data.get("message", "")
                label = str(label_raw or "")
                status_history.append({"phase": phase, "label": label})
                if (phase == "action_message" or "action_message" in event_data) and label:
                    action_messages.append(label)
            elif event_type == AgentStreamEventType.ACTION_MESSAGE:
                message = str(event_data.get("message", "") or "")
                label = str(event_data.get("label", "") or "")
                phase = str(event_data.get("phase", "") or "action_message")
                if message:
                    action_messages.append(message)
                    if label:
                        action_message_labels.append(label)
                    status_history.append(
                        {
                            "phase": phase,
                            "label": label,
                            "message": message,
                        }
                    )
            elif event_type == AgentStreamEventType.SCHEMES_UPDATE:
                schemes = event_data.get("schemes", [])
                if isinstance(schemes, list):
                    final_schemes = schemes
                history = event_data.get("search_history", [])
                if isinstance(history, list):
                    search_history = history
            elif event_type == AgentStreamEventType.SCHEMES:
                history = event_data.get("schemes_history", [])
                if isinstance(history, list):
                    schemes_history = history
                    if history and isinstance(history[-1], list):
                        final_schemes = history[-1]
            elif event_type == AgentStreamEventType.FOLLOWUPS:
                items = event_data.get("items", {})
                if isinstance(items, dict):
                    followups = items

        if not assistant_text and buffered_chunks:
            assistant_text = "".join(buffered_chunks)

        response_payload = {
            "response": True,
            "sessionID": session_id,
            "message": assistant_text,
            "action_message": action_messages[-1] if action_messages else "",
            "action_message_label": action_message_labels[-1] if action_message_labels else "",
            "schemes": final_schemes,
            "schemes_history": schemes_history,
            "total_count": len(final_schemes),
            "search_history": search_history,
            "tool_history": tool_history,
            "followups": followups,
            "status_history": status_history,
            "action_messages": action_messages,
            "action_message_labels": action_message_labels,
        }
        return https_fn.Response(
            response=safe_json_dumps(response_payload),
            status=200,
            mimetype="application/json",
            headers=headers,
        )

    except Exception as exc:
        logger.exception("Error in agent_chat_message", exc)
        return https_fn.Response(
            response=safe_json_dumps({"error": "Internal server error"}),
            status=500,
            mimetype="application/json",
            headers=headers,
        )
