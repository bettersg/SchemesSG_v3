from types import SimpleNamespace

from agent.tools.filter_rerank import filter_rerank_by_directive
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def _tool_call(name: str, call_id: str) -> dict:
    return {"name": name, "args": {}, "id": call_id, "type": "tool_call"}


def test_filter_is_blocked_after_search_in_the_same_turn(mocker):
    retrieve = mocker.patch("agent.tools.filter_rerank._retrieve_search_results_by_doc_id")
    runtime = SimpleNamespace(
        state={
            "messages": [
                HumanMessage(content="Find family support; only show the top 10"),
                AIMessage(
                    content="",
                    tool_calls=[
                        _tool_call("search_schemes", "search-1"),
                        _tool_call("filter_rerank_by_directive", "filter-1"),
                    ],
                ),
            ]
        }
    )

    result = filter_rerank_by_directive("doc-1", "Keep the top 10", runtime=runtime)

    assert result == {"error": "Fresh search results cannot be filtered in the same turn."}
    retrieve.assert_not_called()


def test_filter_is_allowed_for_a_later_user_refinement(mocker):
    schemes = [{"scheme": f"Scheme {index}"} for index in range(20)]
    mocker.patch("agent.tools.filter_rerank._retrieve_search_results_by_doc_id", return_value=schemes)
    mocker.patch(
        "agent.tools.filter_rerank._filter_rerank",
        return_value={"indices": list(range(10)), "llm_response": "[0,1,2,3,4,5,6,7,8,9]"},
    )
    mocker.patch("agent.tools.filter_rerank._save_filtered_reranked_schemes", return_value="filtered-1")
    writer = mocker.patch("agent.tools.filter_rerank.get_stream_writer").return_value
    runtime = SimpleNamespace(
        state={
            "messages": [
                HumanMessage(content="Find family support"),
                AIMessage(content="", tool_calls=[_tool_call("search_schemes", "search-1")]),
                ToolMessage(content="results", tool_call_id="search-1"),
                HumanMessage(content="I only want the top 10"),
                AIMessage(content="", tool_calls=[_tool_call("filter_rerank_by_directive", "filter-1")]),
            ]
        }
    )

    result = filter_rerank_by_directive("doc-1", "Keep the top 10", runtime=runtime)

    assert len(result["schemes"]) == 10
    assert any(call.args[0].get("type") == "schemes_update" for call in writer.call_args_list)
