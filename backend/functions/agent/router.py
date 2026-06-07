from typing import Annotated, Any, TypedDict


import hashlib
import json
from typing import Any


from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import CachePolicy
from .firestore_saver import FirestoreChatSaver
from .tools import (
    search_schemes_tool,
    filter_rerank_by_directive_tool,
    retrieve_schemes_by_ids_tool,
    duckduckgo_web_search_tool,
    load_skills_tool,
)
from .followup import FollowupSubgraph
from .cache import InMemoryCacheWithMaxsize
from integrations import LLMManager
from utils.logging_setup import setup_logging
from .prompts.router import ROUTER_AGENT_SYSTEM_TEMPLATE


logger = setup_logging()
MODEL_NAME = "gpt-5.4-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_COMPLETION_TOKENS = 400


class RouterAgentState(TypedDict):
    messages: Annotated[list[AIMessage | HumanMessage | SystemMessage], add_messages]


class RouterAgentGraph:
    """Main agent graph that encapsulates the full agent loop with tools and follow-up logic."""

    def __init__(self, *, firestore_client: Any | None = None, cache_maxsize: int = 1000):
        self._tools = [
            search_schemes_tool,
            filter_rerank_by_directive_tool,
            retrieve_schemes_by_ids_tool,
            duckduckgo_web_search_tool,
            load_skills_tool,
        ]
        self._checkpointer = FirestoreChatSaver(client=firestore_client) if firestore_client is not None else None
        self._cache = InMemoryCacheWithMaxsize(maxsize=cache_maxsize)
        self.graph = self._build_graph()

    @staticmethod
    def initial_state() -> RouterAgentState:
        return {
            "messages": [],
        }

    def _build_llm_with_tools(self):
        llm_loader = LLMManager(MODEL_NAME)
        llm_loader.modify_llm(
            **{
                "temperature": DEFAULT_TEMPERATURE,
                "max_tokens": DEFAULT_MAX_COMPLETION_TOKENS,
            }
        )
        llm = llm_loader.get_llm()
        return llm.bind_tools(self._tools, parallel_tool_calls=True)

    def call_chat_llm(self, state: RouterAgentState) -> dict[str, Any]:
        llm_with_tools = self._build_llm_with_tools()
        all_messages = state.get("messages", [])
        try:
            response = llm_with_tools.invoke([SystemMessage(ROUTER_AGENT_SYSTEM_TEMPLATE)] + all_messages)
        except Exception as err:
            raise RuntimeError(f"LLM invocation failed: {err}") from err

        return {"messages": [response]}

    @staticmethod
    def _route_after_agent(state: RouterAgentState) -> str:
        last = state.get("messages", [])[-1] if state.get("messages") else None
        tool_calls = getattr(last, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            return "tools"
        return "followup_subgraph"

    def _build_graph(self):
        from langgraph.config import get_stream_writer

        followup_subgraph = FollowupSubgraph().get_subgraph()

        def run_followup(state) -> dict[str, Any]:
            result = followup_subgraph.invoke(state)
            try:
                writer = get_stream_writer()
                writer(
                    {
                        "type": "followups",
                        "data": {
                            "items": json.loads(result["messages"][-1].content) if result.get("messages") else {}
                        },
                    },
                )
            except RuntimeError:
                # Some execution paths run outside a stream-writer context.
                pass
            followup_message = result["messages"][-1] if isinstance(result, dict) and result.get("messages") else None
            if followup_message is None:
                return {"followup_result": {"messages": []}}
            return {"followup_result": {"messages": [followup_message]}}

        builder = StateGraph(RouterAgentState)
        builder.add_node("agent", self.call_chat_llm, cache_policy=CachePolicy())
        builder.add_node("tools", ToolNode(self._tools))
        builder.add_node("followup_subgraph", run_followup)

        builder.add_edge(START, "agent")
        builder.add_conditional_edges(
            "agent",
            self._route_after_agent,
            {
                "tools": "tools",
                "followup_subgraph": "followup_subgraph",
            },
        )
        builder.add_edge("tools", "agent")
        builder.add_edge("followup_subgraph", END)
        return builder.compile(checkpointer=self._checkpointer, cache=self._cache)
