import json
import logging
import re

from langgraph.graph.state import StateGraph, START
from integrations.llm_manager import LLMManager
from .prompts.followup import (
    FOLLOWUP_SYSTEM_TEMPLATE,
    FOLLOWUP_PROMPT_TEMPLATE,
)
from .context_manager import RouterAgentState

MAX_FOLLOWUP_KV = 3
DEFAULT_FOLLOWUP_MAX_COMPLETION_TOKENS = 400
MODEL_TEMPERATURE = 0.7
MODEL_NAME = "gpt-5.4-mini"
BRACKETED_PLACEHOLDER_PATTERN = re.compile(r"\[([^\[\]]+)\]")

# Scripts that signal a non-English conversation language. We key off the
# user's own messages only — the scheme data is full of CJK/Tamil names and
# would otherwise flip suggestions to the wrong language on English chats.
_CJK_PATTERN = re.compile(r"[一-鿿㐀-䶿]")  # Han characters
_TAMIL_PATTERN = re.compile(r"[஀-௿]")
_LATIN_WORD_PATTERN = re.compile(r"[A-Za-z]{2,}")  # an English-ish word


def detect_user_language(human_text: str) -> str:
    """Best-effort language label from the user's own writing.

    English-first for mixed queries: we only pick a non-English language when
    that script clearly dominates the message. A few Latin proper nouns (scheme
    or agency names like "ComCare") in an otherwise Chinese message stay
    Chinese, but a genuinely mixed English+Chinese query resolves to English.
    Latin-script input (including Malay) defaults to English.
    """
    english_words = len(_LATIN_WORD_PATTERN.findall(human_text))

    # Mixed queries prioritise English: two or more English words is enough to
    # stay English even alongside Chinese or Tamil. A genuine Chinese/Tamil
    # message carries at most a stray Latin proper noun (e.g. "ComCare"), so it
    # falls through to the script check below.
    if english_words >= 2:
        return "English"
    if _CJK_PATTERN.search(human_text):
        return "Chinese"
    if _TAMIL_PATTERN.search(human_text):
        return "Tamil"
    return "English"


def parse_schemes_json(schemes_json: object) -> str:
    """Defensively parse various shapes of `current_results_json` and
    return a readable string for the followup prompt.

    Accepts:
    - dict with a top-level `data` list of scheme objects
    - JSON string encoding the above
    - a pre-formatted string (returned as-is)
    """
    if not schemes_json:
        return ""

    # If already a dict-like object, try to extract `data`.
    try:
        if isinstance(schemes_json, dict):
            parsed = schemes_json
        else:
            parsed = json.loads(schemes_json)  # type: ignore[arg-type]
    except Exception:
        # Not JSON — treat as pre-formatted string
        try:
            return str(schemes_json)
        except Exception:
            logging.exception("Failed to interpret schemes_json; returning empty string")
            return ""

    try:
        data = parsed.get("data") if isinstance(parsed, dict) else None
        if isinstance(data, list):
            return "\n".join(
                [
                    f"Scheme Name: {item.get('scheme', 'Unnamed Scheme')} - Scheme Description: {item.get('description', 'No description')}"
                    for item in data
                    if isinstance(item, dict)
                ]
            )
    except Exception:
        logging.exception("Failed to parse schemes JSON for follow-up prompt. Using raw string format.")

    # Fallback: return a simple string representation
    try:
        return json.dumps(parsed) if isinstance(parsed, (dict, list)) else str(parsed)
    except Exception:
        return str(parsed)


def remove_square_bracket_placeholders(text: str) -> str:
    return BRACKETED_PLACEHOLDER_PATTERN.sub(r"\1", text)


def sanitize_followup_content(content: object) -> object:
    try:
        followups = json.loads(content) if isinstance(content, str) else content
    except Exception:
        return remove_square_bracket_placeholders(str(content))

    if not isinstance(followups, dict):
        return content

    sanitized = {
        remove_square_bracket_placeholders(str(key)): remove_square_bracket_placeholders(str(value))
        for key, value in followups.items()
    }
    return json.dumps(sanitized)


def replace_message_content(message, content: object):
    if hasattr(message, "model_copy"):
        return message.model_copy(update={"content": content})
    if hasattr(message, "copy"):
        return message.copy(update={"content": content})
    message.content = content
    return message


class FollowupSubgraph:
    def __init__(self):
        self.subgraph_builder = StateGraph(RouterAgentState)
        llm_loader = LLMManager(MODEL_NAME)
        llm_loader.modify_llm(
            **{
                "temperature": MODEL_TEMPERATURE,
                "max_tokens": DEFAULT_FOLLOWUP_MAX_COMPLETION_TOKENS,
            }
        )
        self.llm = llm_loader.get_llm()

        self.subgraph_builder.add_node("followup_bot", self.followup_bot)
        self.subgraph_builder.add_edge(START, "followup_bot")
        self.subgraph = self.subgraph_builder.compile()

    def invoke(self, state: RouterAgentState):
        return self.subgraph.invoke(state)

    def followup_bot(self, state: RouterAgentState):
        # Determine language from the user's own (human) messages only. The
        # scheme list and even the assistant's replies carry CJK/Tamil scheme
        # names that would otherwise flip English chats to Chinese suggestions.
        human_text = " ".join(
            str(msg.content) for msg in state["messages"] if msg.type == "human"
        )
        language = detect_user_language(human_text)
        system_message = FOLLOWUP_SYSTEM_TEMPLATE.format(
            max_pairs=MAX_FOLLOWUP_KV, language=language
        )
        # Exclude tool messages: scheme data often contains Chinese/Malay names
        # and descriptions, which would otherwise skew the suggestion language.
        transcript = "\n".join(
            [f"{msg.type}: {msg.content}" for msg in state["messages"] if msg.type in ["human", "ai"]]
        )
        parsed_schemes = parse_schemes_json(state.get("current_results_json", ""))
        prompt = FOLLOWUP_PROMPT_TEMPLATE.format(schemes_json=parsed_schemes, transcript=transcript)
        response = self.llm.invoke(
            [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ]
        )
        response = replace_message_content(response, sanitize_followup_content(response.content))
        return {
            "messages": [response]
        }

    def get_subgraph(self):
        return self.subgraph
