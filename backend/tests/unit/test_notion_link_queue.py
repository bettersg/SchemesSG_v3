"""Unit tests for the Notion Link Queue pull sync and weekly metrics row."""

from copy import deepcopy
from datetime import date

import pytest
from batch_jobs import notion_link_queue as nlq


CFG = {"token": "secret", "link_queue": "ds-queue", "metrics": "ds-metrics"}


class FakeNotion(nlq.NotionClient):
    """In-memory Notion behind the real client's request seam (page size 2 to exercise pagination)."""

    def __init__(self):
        self.pages = {}
        self.calls = []

    def _call(self, method, path, body=None):
        self.calls.append((method, path))
        if path.endswith("/query"):
            data_source = path.split("/")[2]
            rows = [page for page in self.pages.values() if page["parent"] == data_source]
            start = int(body.get("start_cursor") or 0)
            more = start + 2 < len(rows)
            return {
                "results": deepcopy(rows[start : start + 2]),
                "has_more": more,
                "next_cursor": str(start + 2) if more else None,
            }
        if method == "POST" and path == "/pages":
            page_id = f"page-{len(self.pages) + 1}"
            self.pages[page_id] = {"id": page_id, "parent": body["parent"]["data_source_id"], "properties": {}}
            self._apply(page_id, body["properties"])
            return deepcopy(self.pages[page_id])
        if method == "PATCH":
            page_id = path.split("/")[2]
            self._apply(page_id, body["properties"])
            return deepcopy(self.pages[page_id])
        raise AssertionError(f"Unexpected Notion call {method} {path}")

    def _apply(self, page_id, properties):
        for name, value in properties.items():
            kind = next(iter(value))
            stored = value[kind]
            if kind in ("title", "rich_text"):
                stored = [{**part, "plain_text": part["text"]["content"]} for part in stored]
            self.pages[page_id]["properties"][name] = {"type": kind, kind: stored}

    def set_human(self, page_id, **values):
        """Simulate a volunteer editing human-owned columns."""
        types = {"Verdict": "select", "Note": "rich_text"}
        self._apply(page_id, nlq.encode_properties(values, types))

    def rows(self, data_source="ds-queue"):
        return {
            nlq.decode_property(page["properties"]["Scheme ID"]): {
                name: nlq.decode_property(prop) for name, prop in page["properties"].items()
            }
            for page in self.pages.values()
            if page["parent"] == data_source
        }

    def page_id(self, scheme_id):
        return next(
            pid
            for pid, page in self.pages.items()
            if "Scheme ID" in page["properties"] and nlq.decode_property(page["properties"]["Scheme ID"]) == scheme_id
        )

    def writes(self):
        return [call for call in self.calls if call[0] in ("POST", "PATCH") and not call[1].endswith("/query")]


@pytest.fixture(autouse=True)
def no_sleep(mocker):
    mocker.patch.object(nlq.time, "sleep", return_value=None)


def _failing(name, **extra):
    return {
        "scheme": name,
        "agency": "Agency",
        "link": f"https://example.org/{name}",
        "status": "inactive",
        "status_reason": "Dead link (hard_dead, 2 consecutive checks)",
        "link_check_status_code": 404,
        "link_check_error": "Not Found",
        "link_check_fail_streak": 2,
        "link_check_fail_class": "hard_dead",
        "last_link_check": "2026-10-05T09:01:00+00:00",
        **extra,
    }


@pytest.mark.parametrize(
    "env",
    [
        {"FB_PROJECT_ID": "schemessg"},  # token unset
        {
            "FB_PROJECT_ID": "schemessg-v3-dev",
            "NOTION_API_TOKEN": "secret",
            "NOTION_LINK_QUEUE_DATA_SOURCE_ID": "ds-queue",
            "NOTION_METRICS_DATA_SOURCE_ID": "ds-metrics",
        },
    ],
    ids=["token_unset", "dev_project"],
)
def test_noop_unless_prod_configured(env, monkeypatch, mocker):
    for name in ("NOTION_API_TOKEN", "NOTION_LINK_QUEUE_DATA_SOURCE_ID", "NOTION_METRICS_DATA_SOURCE_ID"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    db = mocker.MagicMock()
    session = mocker.patch.object(nlq.requests, "Session")

    assert nlq.run_notion_link_queue_sync_core(db) == {"skipped": True}
    assert nlq.append_metrics_row(db, 1, 1) is None
    db.collection.assert_not_called()
    session.assert_not_called()


def test_prod_config_requires_prod_project(monkeypatch):
    monkeypatch.setenv("FB_PROJECT_ID", "schemessg")
    monkeypatch.setenv("NOTION_API_TOKEN", "secret")
    monkeypatch.setenv("NOTION_LINK_QUEUE_DATA_SOURCE_ID", "ds-queue")
    monkeypatch.setenv("NOTION_METRICS_DATA_SOURCE_ID", "ds-metrics")

    assert nlq.notion_config() == CFG


def test_pull_creates_paginates_resolves_and_never_writes_human_columns(fake_firestore):
    for n in range(1, 4):
        fake_firestore.seed("schemes", f"s{n}", _failing(f"scheme-{n}"))
    fake_firestore.seed(
        "schemes", "suspect", _failing("suspect", status=None, link_suspect=True, link_check_fail_streak=1)
    )
    fake_firestore.seed("schemes", "healthy", {"scheme": "Healthy", "link": "https://example.org/ok"})
    fake_firestore.seed("schemes", "retired", _failing("retired", status="retired"))
    notion = FakeNotion()

    first = nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    rows = notion.rows()
    assert first["created"] == 4 and set(rows) == {"s1", "s2", "s3", "suspect"}
    assert rows["s1"] | {"Last synced": None} == {
        "Scheme": "scheme-1",
        "Scheme ID": "s1",
        "Link": "https://example.org/scheme-1",
        "Agency": "Agency",
        "Firestore status": "inactive",
        "Fail class": "hard_dead",
        "Status code": 404,
        "Error": "Not Found",
        "Fail streak": 2,
        "Status reason": "Dead link (hard_dead, 2 consecutive checks)",
        "Last checked": "2026-10-05",
        "Sync state": "Open",
        "Last synced": None,
    }
    assert rows["suspect"]["Firestore status"] == "active"  # missing status = searchable legacy

    # Second run with nothing changed reads every page (pagination) and writes nothing.
    notion.calls.clear()
    second = nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    assert second["rows"] == 4
    assert notion.writes() == []
    assert len([c for c in notion.calls if c[1].endswith("/query")]) == 2

    # A volunteer writes a note; s1 recovers; s2's error changes.
    notion.set_human(notion.page_id("s1"), Note="Checked the agency site")
    fake_firestore.seed("schemes", "s1", {"scheme": "scheme-1", "link": "https://example.org/scheme-1"})
    fake_firestore.seed("schemes", "s2", _failing("scheme-2", link_check_error="Gone", link_check_fail_streak=3))
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    rows = notion.rows()
    assert rows["s1"]["Sync state"] == "Resolved"
    assert rows["s1"]["Sync message"] == "Link is working again"
    assert rows["s1"]["Note"] == "Checked the agency site"
    assert rows["s2"]["Error"] == "Gone" and rows["s2"]["Fail streak"] == 3
    assert rows["s2"]["Sync state"] == "Open"


def test_resolved_row_reopens_when_scheme_fails_again(fake_firestore):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))
    notion = FakeNotion()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    fake_firestore.seed("schemes", "s1", {"scheme": "scheme-1", "link": "https://example.org/scheme-1"})
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    notion.set_human(notion.page_id("s1"), Verdict="Checker wrong")

    fake_firestore.seed("schemes", "s1", _failing("scheme-1", status=None, link_suspect=True))
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Verdict"]) == ("Open", None)
    assert row["Sync message"] == "Failing the link check again"
    assert len(notion.rows()) == 1


@pytest.mark.parametrize(
    ("scheme", "message"),
    [(None, "Scheme no longer exists"), (_failing("x", status="retired"), "Scheme retired")],
    ids=["missing", "retired"],
)
def test_row_for_missing_or_retired_scheme_resolves_once(scheme, message, fake_firestore):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))
    notion = FakeNotion()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    fake_firestore._documents["schemes"].pop("s1")
    if scheme:
        fake_firestore.seed("schemes", "s1", scheme)

    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    notion.calls.clear()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Sync message"]) == ("Resolved", message)
    assert notion.writes() == []


def test_one_bad_row_does_not_abort_the_run(fake_firestore, mocker):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))
    fake_firestore.seed("schemes", "s2", _failing("scheme-2"))
    notion = FakeNotion()
    real_create = notion.create_page
    calls = {"n": 0}

    def flaky_create(data_source_id, properties):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("Notion POST /pages -> 400")
        return real_create(data_source_id, properties)

    mocker.patch.object(notion, "create_page", side_effect=flaky_create)

    result = nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    assert (result["errors"], result["created"]) == (1, 1)


def test_long_error_text_is_truncated_to_notion_limit(fake_firestore):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1", link_check_error="x" * 5000))
    notion = FakeNotion()

    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    notion.calls.clear()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    assert len(notion.rows()["s1"]["Error"]) == nlq.MAX_TEXT
    assert notion.writes() == []


def test_metrics_upsert_by_iso_week_counts_and_latest(fake_firestore):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))
    fake_firestore.seed(
        "schemes", "s2", _failing("scheme-2", status=None, link_suspect=True, link_check_fail_streak=1)
    )
    fake_firestore.seed("schemes", "s3", {"scheme": "Healthy", "status": "active"})
    fake_firestore.seed("schemes", "s4", {"scheme": "Retired", "status": "retired"})
    fake_firestore.seed("schemeEntries", "e1", {"pipeline_status": "failed"})
    fake_firestore.seed("schemeEntries", "e2", {"pipeline_status": "completed"})
    fake_firestore.seed("userFeedback", "f1", {"feedbackText": "hi"})
    notion = FakeNotion()

    last_week = nlq.append_metrics_row(fake_firestore, 0, 0, cfg=CFG, notion=notion, today=date(2026, 9, 28))
    first = nlq.append_metrics_row(fake_firestore, 2, 1, cfg=CFG, notion=notion, today=date(2026, 10, 5))
    # The link job has retry_count=1: a second run in the same ISO week updates, never duplicates.
    rerun = nlq.append_metrics_row(fake_firestore, 2, 1, cfg=CFG, notion=notion, today=date(2026, 10, 6))

    assert first == rerun != last_week

    rows = {
        nlq.decode_property(page["properties"]["Week"]): {
            name: nlq.decode_property(prop) for name, prop in page["properties"].items()
        }
        for page in notion.pages.values()
    }
    assert set(rows) == {"2026-W40", "2026-W41"}
    assert rows["2026-W40"]["Latest"] is False
    assert rows["2026-W41"] == {
        "Week": "2026-W41",
        "Snapshot date": "2026-10-06",
        "Latest": True,
        "Total schemes": 4,
        "Searchable": 2,
        "Inactive": 1,
        "Retired": 1,
        "Suspect": 1,
        "Newly inactivated": 2,
        "Restored": 1,
        "Queue open": 2,
        "Verdicts this week": 0,
        "Submissions failed": 1,
        "Feedback total": 1,
    }


def test_iso_week_uses_iso_year():
    assert nlq._iso_week(date(2029, 12, 31)) == "2030-W01"
