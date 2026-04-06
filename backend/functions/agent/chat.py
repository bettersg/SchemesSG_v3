"""Agent chat endpoint backed by the runtime streaming module.

Local URL (emulator):
http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/agent_chat_message
"""

from __future__ import annotations

import json
import re
from uuid import uuid1

from firebase_functions import https_fn, options
from utils.auth import verify_auth_token
from utils.cors_config import get_cors_headers, handle_cors_preflight
from utils.json_utils import safe_json_dumps
from utils.logging_setup import setup_logging

from .event_type import AgentStreamEventType
from .main import stream_chat_events_sync


logger = setup_logging()


def _split_stream_chunk(text: str) -> list[str]:
    """Split chunk text into smaller token-like pieces for SSE UX.

    This keeps leading spaces attached to tokens after the first piece, matching
    common incremental rendering behavior in the frontend.
    """

    if not text:
        return []

    parts = re.findall(r"\s*[A-Za-z0-9]+|\s*[’'][A-Za-z0-9]+|\s*[^\w\s]", text)
    return parts if parts else [text]


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
                emitted_chunk = False
                done_emitted = False
                yield f"data: {safe_json_dumps({'type': AgentStreamEventType.STATUS, 'data': {'phase': 'session_started', 'sessionID': session_id, 'label': 'Session started'}})}\n\n"
                try:
                    for event in stream_chat_events_sync(input_text=input_text, session_id=session_id):
                        event_type = event.get("type", "")
                        event_data = event.get("data", {})
                        if not isinstance(event_data, dict):
                            event_data = {}

                        if event_type == AgentStreamEventType.DONE:
                            done_emitted = True

                        if event_type == AgentStreamEventType.CHUNK:
                            chunk_value = str(event_data.get("chunk", "") or "")
                            for piece in _split_stream_chunk(chunk_value):
                                yield f"data: {safe_json_dumps({'type': AgentStreamEventType.CHUNK, 'data': {'chunk': piece}})}\n\n"
                                emitted_chunk = True
                            continue

                        # Some runs may only surface final assistant text.
                        if event_type == AgentStreamEventType.ASSISTANT:
                            assistant_text = str(event_data.get("text", "") or "")
                            if not emitted_chunk:
                                for piece in _split_stream_chunk(assistant_text):
                                    yield f"data: {safe_json_dumps({'type': AgentStreamEventType.CHUNK, 'data': {'chunk': piece}})}\n\n"
                            continue

                        # Forward non-chunk events with explicit type/data for frontend handling.
                        yield f"data: {safe_json_dumps({'type': event_type, 'data': event_data})}\n\n"
                except GeneratorExit:
                    raise
                except Exception as exc:
                    logger.exception("Error while streaming agent chat events", exc)
                    yield f"data: {safe_json_dumps({'type': AgentStreamEventType.STATUS, 'data': {'phase': 'error', 'label': 'Stream interrupted'}})}\n\n"

                if not done_emitted:
                    yield f"data: {safe_json_dumps({'type': AgentStreamEventType.DONE, 'data': {}})}\n\n"

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
        buffered_chunks: list[str] = []

        for event in stream_chat_events_sync(input_text=input_text, session_id=session_id):
            event_type = event.get("type", "")
            event_data = event.get("data", {})
            if not isinstance(event_data, dict):
                event_data = {}
            if event_type == AgentStreamEventType.CHUNK:
                chunk = event_data.get("chunk", "")
                if isinstance(chunk, str) and chunk:
                    buffered_chunks.append(chunk)
            elif event_type == AgentStreamEventType.ASSISTANT:
                assistant_text = str(event_data.get("text", "") or "")
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
            "schemes": final_schemes,
            "schemes_history": schemes_history,
            "total_count": len(final_schemes),
            "search_history": search_history,
            "tool_history": tool_history,
            "followups": followups,
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
