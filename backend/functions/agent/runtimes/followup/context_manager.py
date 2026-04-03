"""Context helpers for follow-up suggestion generation."""

from __future__ import annotations

from typing import Any

TRANSCRIPT_MAX_ITEMS = 20



def messages_to_transcript(messages: list[object], max_items: int = TRANSCRIPT_MAX_ITEMS) -> str:
    lines: list[str] = []
    for msg in messages[-max_items:]:
        msg_type = getattr(msg, "type", type(msg).__name__)
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            content = "\n".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
        role = "assistant" if msg_type in {"ai", "assistant"} else "user"
        text = str(content).strip()
        if not text:
            continue
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def normalize_key(key: str, used: set[str], fallback_idx: int) -> str:
    words = [w for w in str(key).strip().split() if w]
    if not words:
        base = f"Question {fallback_idx}"
    else:
        base = " ".join(words[:3])

    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base} {suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def normalize_followups_map(raw_map: dict[str, Any], max_items: int) -> dict[str, str]:
    normalized: dict[str, str] = {}
    used_keys: set[str] = set()

    idx = 1
    for key, value in raw_map.items():
        question = str(value).strip()
        if not question:
            continue
        label = normalize_key(str(key), used_keys, idx)
        normalized[label] = question
        idx += 1
        if len(normalized) >= max_items:
            break

    return normalized
