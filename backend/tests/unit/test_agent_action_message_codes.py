"""Unit tests for the codes on the agent's status steps.

Behaviour under test: every action_message a tool streams carries a stable
`code` and its `params`, which the chat UI uses to show the step in the user's
language, alongside the English `label` and `message` that remain the fallback.
Network and Firestore are not touched: the download and search clients are
replaced, and the empty-input path of scheme retrieval needs neither.
"""

from unittest import mock

from agent.tools import fetch_webpage, retrieve_scheme, websearch


def _steps(events):
    return [(event["data"]["code"], event["data"]["params"]) for event in events]


def test_unreadable_page_reports_start_then_fail():
    events = []
    with mock.patch.object(fetch_webpage, "get_stream_writer", return_value=events.append), mock.patch.object(
        fetch_webpage, "_download_html", return_value=None
    ):
        fetch_webpage._fetch_webpage_sync("https://example.org/aid")

    assert _steps(events) == [
        ("fetch.start", {"url": "https://example.org/aid"}),
        ("fetch.fail", {"url": "https://example.org/aid"}),
    ]
    assert all(event["data"]["label"] and event["data"]["message"] for event in events)


def test_web_search_reports_its_query_and_result_count():
    events = []
    results = [
        {"title": "Rent help", "link": "https://example.org/rent", "snippet": "Rental support"},
        {"title": "Food help", "link": "https://example.org/food", "snippet": "Food vouchers"},
    ]
    with mock.patch.object(websearch, "get_stream_writer", return_value=events.append), mock.patch.object(
        websearch, "DuckDuckGoSearchResults"
    ) as search_tool:
        search_tool.return_value.invoke.return_value = results
        websearch._duckduckgo_web_search_sync("rent help singapore")

    assert _steps(events) == [
        ("websearch.start", {"query": "rent help singapore"}),
        ("websearch.end", {"count": 2, "query": "rent help singapore"}),
    ]


def test_retrieving_no_schemes_reports_a_zero_count():
    events = []
    with mock.patch.object(retrieve_scheme, "get_stream_writer", return_value=events.append):
        retrieve_scheme.retrieve_schemes_by_ids([" "])

    assert _steps(events) == [("retrieve.start", {}), ("retrieve.end", {"count": 0})]
