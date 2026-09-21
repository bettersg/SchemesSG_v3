"""Context abstractions for the router tool-enabled assistant runtime."""

from __future__ import annotations

import ast
import json
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage, AIMessage
from langgraph.graph.message import add_messages


class RouterAgentState(TypedDict):
    messages: Annotated[list[AIMessage | HumanMessage | SystemMessage], add_messages]
