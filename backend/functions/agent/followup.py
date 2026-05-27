import json
import logging

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
        system_message = FOLLOWUP_SYSTEM_TEMPLATE.format(max_pairs=MAX_FOLLOWUP_KV)
        transcript = "\n".join(
            [f"{msg.type}: {msg.content}" for msg in state["messages"] if msg.type in ["human", "ai", "tool"]]
        )
        parsed_schemes = parse_schemes_json(state.get("current_results_json", ""))
        prompt = FOLLOWUP_PROMPT_TEMPLATE.format(schemes_json=parsed_schemes, transcript=transcript)
        return {
            "messages": [
                self.llm.invoke(
                    [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ]
                )
            ]
        }

    def get_subgraph(self):
        return self.subgraph
