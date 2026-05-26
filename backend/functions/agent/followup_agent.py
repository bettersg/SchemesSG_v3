from typing_extensions import TypedDict, Annotated
from langgraph.graph.state import StateGraph, START
from langgraph.graph.message import add_messages
from integrations.llm_manager import LLMManager
from .prompts.followup import (
    FOLLOWUP_SYSTEM_TEMPLATE,
    FOLLOWUP_PROMPT_TEMPLATE,
)

MAX_FOLLOWUP_KV = 3
DEFAULT_FOLLOWUP_MAX_COMPLETION_TOKENS = 400
MODEL_TEMPERATURE = 0.7
MODEL_NAME = "gpt-5.4-mini"


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


class FollowupSubgraph:
    def __init__(self):
        self.subgraph_builder = StateGraph(State)
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

    def invoke(self, state: State):
        return self.subgraph.invoke(state)

    def followup_bot(self, state: State):
        system_message = FOLLOWUP_SYSTEM_TEMPLATE.format(max_pairs=MAX_FOLLOWUP_KV)
        transcript = "\n".join(
            [f"{msg.type}: {msg.content}" for msg in state["messages"] if msg.type in ["human", "ai"]]
        )
        prompt = FOLLOWUP_PROMPT_TEMPLATE.format(transcript=transcript)
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
