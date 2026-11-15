"""Unit tests for the language of the follow-up suggestions.

Behaviour under test: the suggestions follow the language of the user's latest
message, which is handed to the model on its own. Earlier messages, and scheme
names inside the latest one (English names in a Chinese sentence), must not
decide it. The model call is replaced; only the prompt it receives is checked.
"""

from types import SimpleNamespace
from unittest import mock

from langchain_core.messages import AIMessage

from agent.followup import FollowupSubgraph, latest_user_message


def _message(kind, content):
    return SimpleNamespace(type=kind, content=content)


def test_latest_user_message_is_the_newest_human_turn():
    state = {
        "messages": [
            _message("human", "I need financial assistance"),
            _message("ai", "Here are some schemes."),
            _message("human", "ComCare SMTA 的申请条件是什么？"),
            _message("ai", "ComCare SMTA 需要……"),
        ]
    }

    assert latest_user_message(state) == "ComCare SMTA 的申请条件是什么？"


def test_latest_user_message_is_empty_without_a_human_turn():
    assert latest_user_message({"messages": [_message("ai", "Hello")]}) == ""


def test_prompt_hands_the_latest_message_to_the_model():
    subgraph = FollowupSubgraph.__new__(FollowupSubgraph)
    subgraph.llm = mock.Mock()
    subgraph.llm.invoke.return_value = AIMessage(content='{"比较方案": "比较这些援助计划的补助"}')
    state = {
        "messages": [
            _message("human", "I need financial assistance"),
            _message("ai", "Here are some schemes."),
            _message("human", "ComCare SMTA 的申请条件是什么？"),
        ],
        "current_results_json": "",
    }

    subgraph.followup_bot(state)

    system, user = subgraph.llm.invoke.call_args.args[0]
    assert "{language}" not in system["content"]
    assert "Latest user message" in system["content"]
    latest_section = user["content"].split("Latest user message", 1)[1]
    assert "ComCare SMTA 的申请条件是什么？" in latest_section
    assert "I need financial assistance" not in latest_section
