"""Generic runtime engine for follow-up LLM generation."""

from __future__ import annotations

import json
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from .config import FollowupRuntimeConfig
from .context_manager import messages_to_transcript, normalize_followups_map
from .prompt import DEFAULT_FOLLOWUP_KV, FOLLOWUP_PROMPT_TEMPLATE, FOLLOWUP_SYSTEM_TEMPLATE, MAX_FOLLOWUP_KV


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(text[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _is_content_filter_error(err: Exception) -> bool:
    status_code = getattr(err, "status_code", None)
    body = getattr(err, "body", None)
    if isinstance(body, dict):
        error_obj = body.get("error", {})
        if isinstance(error_obj, dict) and error_obj.get("code") == "content_filter":
            return True

    response = getattr(err, "response", None)
    if response is not None:
        try:
            data = response.json()
            if isinstance(data, dict):
                error_obj = data.get("error", {})
                if isinstance(error_obj, dict) and error_obj.get("code") == "content_filter":
                    return True
        except Exception:
            pass

    err_text = str(err).lower()
    return status_code == 400 and ("content_filter" in err_text or "responsibleaipolicyviolation" in err_text)


class FollowupEngine:
    """Encapsulates follow-up model invocation and normalization."""

    def _build_llm(self):
        cfg = FollowupRuntimeConfig()
        return init_chat_model(
            cfg.provider_model_name,
            azure_deployment=cfg.azure_deployment,
            api_version=cfg.openai_api_version,
            temperature=cfg.temperature,
            model_kwargs={"max_completion_tokens": cfg.max_completion_tokens},
        )

    def generate_kv(self, messages: list[object], max_pairs: int = MAX_FOLLOWUP_KV) -> dict[str, str]:
        llm = self._build_llm()
        system = SystemMessage(content=FOLLOWUP_SYSTEM_TEMPLATE.format(max_pairs=max_pairs))
        transcript = messages_to_transcript(messages)
        prompt = FOLLOWUP_PROMPT_TEMPLATE.format(transcript=transcript)

        try:
            response = llm.invoke([system, HumanMessage(content=prompt)])
        except Exception as err:
            if _is_content_filter_error(err):
                return dict(list(DEFAULT_FOLLOWUP_KV.items())[:max_pairs])
            raise

        content = getattr(response, "content", "")
        if isinstance(content, list):
            content = "\n".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])

        parsed = _extract_json_object(str(content))
        if isinstance(parsed, dict):
            normalized = normalize_followups_map(parsed, max_items=max_pairs)
            if normalized:
                return normalized

        return dict(list(DEFAULT_FOLLOWUP_KV.items())[:max_pairs])

    async def generate_kv_async(self, messages: list[object], max_pairs: int = MAX_FOLLOWUP_KV) -> dict[str, str]:
        llm = self._build_llm()
        system = SystemMessage(content=FOLLOWUP_SYSTEM_TEMPLATE.format(max_pairs=max_pairs))
        transcript = messages_to_transcript(messages)
        prompt = FOLLOWUP_PROMPT_TEMPLATE.format(transcript=transcript)

        try:
            response = await llm.ainvoke([system, HumanMessage(content=prompt)])
        except Exception as err:
            if _is_content_filter_error(err):
                return dict(list(DEFAULT_FOLLOWUP_KV.items())[:max_pairs])
            raise

        content = getattr(response, "content", "")
        if isinstance(content, list):
            content = "\n".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])

        parsed = _extract_json_object(str(content))
        if isinstance(parsed, dict):
            normalized = normalize_followups_map(parsed, max_items=max_pairs)
            if normalized:
                return normalized

        return dict(list(DEFAULT_FOLLOWUP_KV.items())[:max_pairs])
