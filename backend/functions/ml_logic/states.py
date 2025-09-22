from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class ChatbotState(TypedDict):
    messages: Annotated[list, add_messages]
    top_schemes_text: str
    query_text: str
