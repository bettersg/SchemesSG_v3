"""Unit tests for the Notion Link Queue pull sync and weekly metrics row."""

from copy import deepcopy
from datetime import date

import pytest
from batch_jobs import notion_link_queue as nlq


CFG = {"token": "secret", "link_queue": "ds-queue", "metrics": "ds-metrics"}
# Columns volunteers (or the Notion AI agent) own. The sync must never send these, except
# clearing Verdict when a Resolved row reopens.
HUMAN_COLUMNS = {
    "Verdict": "select",
    "New URL": "url",
    "Retire reason": "rich_text",
    "Merged into": "rich_text",
    "Note": "rich_text",
    "AI Triage Hint": "rich_text",
    "Verdict by": "people",
}


class FakeNotion(nlq.NotionClient):
    """In-memory Notion behind the real client's request seam (page size 2 to exercise pagination)."""

    def __init__(self):
        self.pages = {}
        self.calls = []
        self.patches = []  # property payload of every PATCH, to prove which columns the sync touches
        self.users = {"u-alex": {"object": "user", "name": "Alex Tan", "person": {"email": "alex@example.org"}}}

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
            self.patches.append(deepcopy(body["properties"]))
            self._apply(page_id, body["properties"])
            return deepcopy(self.pages[page_id])
        if method == "GET" and path.startswith("/users/"):
            return deepcopy(self.users[path.split("/")[2]])
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
        types = {name: HUMAN_COLUMNS[name] for name in values}
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
        {},
        {"NOTION_API_TOKEN": "secret", "NOTION_LINK_QUEUE_DATA_SOURCE_ID": "ds-queue"},
    ],
    ids=["unset", "metrics_unset"],
)
def test_noop_unless_configured(env, monkeypatch, mocker):
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


@pytest.mark.parametrize("project", ["schemessg", "schemessg-v3-dev"])
def test_config_is_read_in_any_project(project, monkeypatch):
    monkeypatch.setenv("FB_PROJECT_ID", project)
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
        "Weeks failing": 2,
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
    assert rows["s2"]["Error"] == "Gone" and rows["s2"]["Weeks failing"] == 3
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


def test_sync_never_overwrites_volunteer_columns(fake_firestore):
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))
    fake_firestore.seed("schemes", "s2", _failing("scheme-2"))
    notion = FakeNotion()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    edits = {
        "Verdict": "Unclear",
        "New URL": "https://example.org/new",
        "Retire reason": "Ended in 2025",
        "Merged into": "other-scheme",
        "Note": "Checked on Monday",
        "AI Triage Hint": "Search the agency website.",
    }
    for scheme_id in ("s1", "s2"):
        notion.set_human(notion.page_id(scheme_id), **edits)

    # Facts change on s1, s2 recovers (Resolved), then s2 fails again (reopens).
    fake_firestore.seed("schemes", "s1", _failing("scheme-1", link_check_error="Gone", link_check_fail_streak=3))
    fake_firestore.seed("schemes", "s2", {"scheme": "scheme-2", "link": "https://example.org/scheme-2"})
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    fake_firestore.seed("schemes", "s2", _failing("scheme-2"))
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)

    rows = notion.rows()
    assert {name: rows["s1"][name] for name in edits} == edits  # facts refreshed, volunteer work intact
    assert rows["s1"]["Error"] == "Gone"
    assert rows["s2"]["Sync state"] == "Open" and rows["s2"]["Verdict"] is None  # reopen clears only Verdict
    assert rows["s2"]["AI Triage Hint"] == ""  # stale after a reopen; refills on the next edit
    kept = {name for name in edits if name not in ("Verdict", "AI Triage Hint")}
    assert {name: rows["s2"][name] for name in kept} == {name: edits[name] for name in kept}
    for patch in notion.patches:
        touched = set(patch) & set(HUMAN_COLUMNS)
        assert touched <= {"Verdict", "AI Triage Hint"}, touched
        if "Verdict" in patch:
            assert patch["Verdict"] == {"select": None} and patch["Sync state"] == {"select": {"name": "Open"}}
        if "AI Triage Hint" in patch:  # only ever cleared, and only on a reopen or rejection
            assert patch["AI Triage Hint"] == {"rich_text": []}
            assert patch["Sync state"]["select"]["name"] in ("Open", "Rejected")


# --- Verdicts (push) ---------------------------------------------------------

UPDATE_SCHEME_KEYS = {
    "Changes", "Description", "Link", "Scheme", "Status", "entryId", "targetSchemeId", "oldLink",
    "retiredReason", "mergedInto", "timestamp", "userName", "userEmail", "typeOfRequest",
}  # fmt: skip


def _queue_with_row(fake_firestore, scheme_id="s1", **scheme):
    fake_firestore.seed("schemes", scheme_id, _failing("scheme-1", **scheme))
    fake_firestore.seed("schemes", "other", {"scheme": "Other scheme", "link": "https://example.org/other"})
    notion = FakeNotion()
    nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)
    return notion, notion.page_id(scheme_id)


def _verdict(notion, page_id, **values):
    values.setdefault("Verdict by", [{"id": "u-alex"}])
    notion.set_human(page_id, **values)


def _sync(fake_firestore, notion):
    notion.calls.clear()
    return nlq.run_notion_link_queue_sync_core(fake_firestore, cfg=CFG, notion=notion)


def test_moved_verdict_submits_an_update_entry_like_update_scheme(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(
        notion, page_id, Verdict="Moved", **{"New URL": "https://example.org/new-home", "Note": "Moved under services"}
    )

    _sync(fake_firestore, notion)

    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Entry ID"]) == ("Submitted", f"notion-{page_id}-1")
    entry = fake_firestore.get_document("schemeEntries", f"notion-{page_id}-1")
    assert set(entry) == UPDATE_SCHEME_KEYS | {"source"} and "pipeline_status" not in entry
    assert entry["typeOfRequest"] == "update" and entry["targetSchemeId"] == "s1"
    assert (entry["Link"], entry["oldLink"]) == ("https://example.org/new-home", "https://example.org/scheme-1")
    assert (entry["Scheme"], entry["Changes"]) == ("scheme-1", "Moved under services")
    assert (entry["userName"], entry["userEmail"], entry["source"]) == ("Alex Tan", "alex@example.org", nlq.SOURCE)
    # Waiting on the maintainer: the next run reads the entry and writes nothing.
    _sync(fake_firestore, notion)
    assert notion.writes() == []


def test_retire_verdict_submits_a_retire_entry(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, Verdict="Retire", **{"Retire reason": "Programme ended in 2025", "Merged into": "other"})

    _sync(fake_firestore, notion)

    entry = fake_firestore.get_document("schemeEntries", f"notion-{page_id}-1")
    assert entry["typeOfRequest"] == "retire"
    assert (entry["retiredReason"], entry["mergedInto"], entry["oldLink"]) == (
        "Programme ended in 2025",
        "other",
        None,
    )
    assert notion.rows()["s1"]["Sync state"] == "Submitted"


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"Verdict": "Moved"}, "Paste the new web address into New URL."),
        (
            {"Verdict": "Moved", "New URL": "ftp://example.org/x"},
            "New URL must be a full web address starting with https://.",
        ),
        (
            {"Verdict": "Moved", "New URL": "https://www.EXAMPLE.org/scheme-1/"},
            "New URL is the same as the current link.",
        ),
        ({"Verdict": "Retire"}, "Write in Retire reason why the scheme has ended."),
        (
            {"Verdict": "Retire", "Retire reason": "Ended", "Merged into": "no-such-scheme"},
            "Merged into must be the Scheme ID of another scheme that is still listed.",
        ),
        (
            {"Verdict": "Retire", "Retire reason": "Ended", "Merged into": "s1"},
            "Merged into must be the Scheme ID of another scheme that is still listed.",
        ),
    ],
    ids=[
        "moved-no-url",
        "moved-not-http",
        "moved-same-url",
        "retire-no-reason",
        "retire-bad-merge",
        "retire-self-merge",
    ],
)
def test_invalid_verdict_is_rejected_with_a_plain_message(values, message, fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, **values)

    _sync(fake_firestore, notion)
    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Sync message"]) == ("Rejected", message)
    assert fake_firestore.list_documents("schemeEntries") == {}
    # Still invalid: no rewrite every 30 minutes.
    _sync(fake_firestore, notion)
    assert notion.writes() == []
    # Volunteer clears the verdict: back to Open.
    notion.set_human(page_id, Verdict=None)
    _sync(fake_firestore, notion)
    assert notion.rows()["s1"]["Sync state"] == "Open"


def test_checker_wrong_asks_a_maintainer_to_restore_the_link(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    before = fake_firestore.get_document("schemes", "s1")
    _verdict(notion, page_id, Verdict="Checker wrong", Note="Opens fine in a browser")

    _sync(fake_firestore, notion)

    # Nothing changes on the scheme until a maintainer approves in Slack.
    assert fake_firestore.get_document("schemes", "s1") == before
    entry = fake_firestore.get_document("schemeEntries", f"notion-{page_id}-1")
    assert set(entry) == UPDATE_SCHEME_KEYS | {"source"}
    assert (entry["typeOfRequest"], entry["targetSchemeId"], entry["Link"]) == ("restore", "s1", before["link"])
    assert (entry["oldLink"], entry["retiredReason"], entry["Changes"]) == (None, None, "Opens fine in a browser")
    assert notion.rows()["s1"]["Sync state"] == "Submitted"

    # Approval relists the scheme (see approval_handler), so it leaves the failing set.
    fake_firestore.collection("schemeEntries").document(f"notion-{page_id}-1").update({"Status": "approved"})
    fake_firestore.seed("schemes", "s1", {"scheme": "scheme-1", "link": before["link"], "status": "active"})
    _sync(fake_firestore, notion)
    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Sync message"]) == (
        "Resolved",
        "Approved: listed again, and searchable after Monday's reindex",
    )
    _sync(fake_firestore, notion)
    assert notion.writes() == []


def test_unclear_parks_until_the_next_weekly_check(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, Verdict="Unclear", Note="Domain looks new")
    _sync(fake_firestore, notion)
    assert notion.rows()["s1"]["Sync state"] == "Parked"
    _sync(fake_firestore, notion)
    assert notion.writes() == []  # parked while already inactive: no reopen loop

    fake_firestore.seed("schemes", "s1", _failing("scheme-1", last_link_check="2099-01-05T09:01:00+00:00"))
    _sync(fake_firestore, notion)

    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Verdict"], row["Note"]) == ("Open", None, "Domain looks new")
    assert row["Sync message"] == "Still failing after this week's check. Take another look."


def test_parked_row_reopens_when_the_scheme_goes_inactive(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore, status="active", link_check_fail_streak=1, link_suspect=True)
    _verdict(notion, page_id, Verdict="Unclear")
    _sync(fake_firestore, notion)
    # A second hard-dead week delists it.
    fake_firestore.seed("schemes", "s1", _failing("scheme-1"))

    _sync(fake_firestore, notion)
    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Verdict"]) == ("Open", None)
    assert row["Sync message"] == "Went inactive again. Please check it again."
    _sync(fake_firestore, notion)
    assert notion.writes() == []


@pytest.mark.parametrize(
    ("entry_update", "state", "message", "verdict_cleared"),
    [
        ({"Status": "approved", "pipeline_status": "completed"}, "Resolved", "Approved by a maintainer", False),
        (
            {"Status": "rejected", "rejection_reason": "Wrong programme"},
            "Open",
            "A maintainer rejected this: Wrong programme. Check again and choose a verdict.",
            True,
        ),
        ({"Status": "rejected"}, "Open", "A maintainer rejected this. Check again and choose a verdict.", True),
        ({"pipeline_status": "failed"}, "Open", "Processing failed. Choose the verdict again to retry.", True),
        (None, "Open", "The submission was lost. Choose the verdict again.", True),
        ({"pipeline_status": "completed"}, "Submitted", "Sent to a maintainer for approval in Slack", False),
    ],
    ids=["approved", "rejected-reason", "rejected", "failed", "missing", "pending"],
)
def test_submitted_row_follows_the_maintainer_outcome(entry_update, state, message, verdict_cleared, fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, Verdict="Moved", **{"New URL": "https://example.org/new-home"})
    notion.set_human(page_id, **{"AI Triage Hint": "All done: this goes to a maintainer for approval."})
    _sync(fake_firestore, notion)
    entry_id = f"notion-{page_id}-1"
    if entry_update is None:
        fake_firestore._documents["schemeEntries"].pop(entry_id)
    else:
        fake_firestore.collection("schemeEntries").document(entry_id).update(entry_update)
    if (entry_update or {}).get("Status") == "approved":
        # What approval_handler does to the scheme: new link, active, failure state cleared.
        fake_firestore.seed(
            "schemes", "s1", {"scheme": "scheme-1", "link": "https://example.org/new-home", "status": "active"}
        )

    _sync(fake_firestore, notion)

    row = notion.rows()["s1"]
    assert (row["Sync state"], row["Sync message"]) == (state, message)
    assert (row["Verdict"] is None) == verdict_cleared
    assert (row.get("AI Triage Hint") == "") == verdict_cleared  # reopened: the "All done" hint is cleared
    assert row["Entry ID"] == entry_id  # never cleared: the next submission is -2
    assert len(fake_firestore.list_documents("schemeEntries")) == (0 if entry_update is None else 1)


def test_resubmission_after_rejection_and_crash_replay(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    # Crash replay: last run created entry -1 but died before saving Entry ID in Notion.
    fake_firestore.seed("schemeEntries", f"notion-{page_id}-1", {"typeOfRequest": "update", "marker": "first run"})
    _verdict(notion, page_id, Verdict="Moved", **{"New URL": "https://example.org/new-home"})
    _sync(fake_firestore, notion)
    assert notion.rows()["s1"]["Entry ID"] == f"notion-{page_id}-1"
    assert fake_firestore.get_document("schemeEntries", f"notion-{page_id}-1")["marker"] == "first run"

    fake_firestore.collection("schemeEntries").document(f"notion-{page_id}-1").update({"Status": "rejected"})
    _sync(fake_firestore, notion)
    _verdict(notion, page_id, Verdict="Moved", **{"New URL": "https://example.org/newer-home"})
    _sync(fake_firestore, notion)

    assert notion.rows()["s1"]["Entry ID"] == f"notion-{page_id}-2"
    newer = fake_firestore.get_document("schemeEntries", f"notion-{page_id}-2")
    assert newer["Link"] == "https://example.org/newer-home"
    assert len(fake_firestore.list_documents("schemeEntries")) == 2


def test_verdict_on_a_retired_scheme_is_never_applied(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, Verdict="Checker wrong")
    fake_firestore.seed("schemes", "s1", _failing("scheme-1", status="retired"))

    _sync(fake_firestore, notion)

    assert fake_firestore.get_document("schemes", "s1")["status"] == "retired"
    assert notion.rows()["s1"]["Sync state"] == "Resolved"


def test_retire_verdict_is_applied_even_if_the_link_just_recovered(fake_firestore):
    notion, page_id = _queue_with_row(fake_firestore)
    _verdict(notion, page_id, Verdict="Retire", **{"Retire reason": "Programme ended"})
    fake_firestore.seed("schemes", "s1", {"scheme": "scheme-1", "link": "https://example.org/scheme-1"})

    _sync(fake_firestore, notion)

    assert notion.rows()["s1"]["Sync state"] == "Submitted"
    assert fake_firestore.get_document("schemeEntries", f"notion-{page_id}-1")["typeOfRequest"] == "retire"
