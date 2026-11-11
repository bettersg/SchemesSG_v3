"""Unit tests for the daily Review Leaderboard sync to the Better.sg Notion workspace."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from batch_jobs import review_leaderboard as lb
from batch_jobs.notion_client import NotionClient, decode_row
from slack_sdk.errors import SlackApiError

from tests.fakes import FakeFirestore


NOW = datetime(2026, 11, 11, 5, 0, tzinfo=timezone.utc)
DS = lb.DATA_SOURCE_ID


class FakeNotion(NotionClient):
    """In-memory Notion behind the real client's request seam (one user per page to exercise paging)."""

    def __init__(self, pages=None, users=None):
        self.pages = {page["id"]: page for page in deepcopy(pages or [])}
        self.users = users or []
        self.calls = []

    def _call(self, method, path, body=None):
        self.calls.append((method, path))
        if path.startswith("/users"):
            start = int(path.split("start_cursor=")[1]) if "start_cursor=" in path else 0
            more = start + 1 < len(self.users)
            return {"results": self.users[start : start + 1], "has_more": more, "next_cursor": str(start + 1)}
        if path == f"/data_sources/{DS}/query":
            return {"results": deepcopy(list(self.pages.values())), "has_more": False}
        if method == "POST" and path == "/pages":
            page_id = f"page-{len(self.pages) + 1}"
            self.pages[page_id] = {"id": page_id, "properties": {}}
            self._apply(page_id, body)
            return deepcopy(self.pages[page_id])
        if method == "PATCH" and path.startswith("/pages/"):
            self._apply(path.split("/")[2], body)
            return {}
        raise AssertionError(f"unexpected Notion call {method} {path}")

    def _apply(self, page_id, body):
        page = self.pages[page_id]
        page["icon"] = body.get("icon")
        for name, prop in body["properties"].items():
            kind, value = next(iter(prop.items()))
            if kind in ("title", "rich_text"):
                value = [{**part, "plain_text": part["text"]["content"]} for part in value]
            page["properties"][name] = {"type": kind, kind: value}


class FakeSlack:
    USERS = {
        "U-ann": {"id": "U-ann", "name": "ann", "profile": {"display_name": "Ann", "email": "ann@example.org"}},
        "U-bo": {"id": "U-bo", "real_name": "Bo Tan", "profile": {"display_name": "", "email": "bo@example.org"}},
    }

    def users_info(self, *, user):
        if user not in self.USERS:
            raise SlackApiError("user_not_found", {"ok": False, "error": "user_not_found"})
        return {"ok": True, "user": self.USERS[user]}

    def users_lookupByEmail(self, *, email):
        for user in self.USERS.values():
            if user["profile"]["email"] == email:
                return {"ok": True, "user": user}
        raise SlackApiError("users_not_found", {"ok": False, "error": "users_not_found"})


def page_for(key, page_id="page-1"):
    return {
        "id": page_id,
        "properties": {"Reviewer key": {"type": "rich_text", "rich_text": [{"plain_text": key}]}},
    }


def test_aggregate_counts_this_month_in_sgt_and_keeps_latest_review():
    nov_1_sgt = datetime(2026, 10, 31, 17, tzinfo=timezone.utc)  # 01:00 on 1 Nov in Singapore
    oct_31_sgt = datetime(2026, 10, 31, 15, tzinfo=timezone.utc)
    latest = NOW - timedelta(days=1)
    stats = lb.aggregate(
        [
            ("U1", "Approved", nov_1_sgt),
            ("U1", "Approved", oct_31_sgt),
            ("U1", "Rejected", latest),
            ("U2", "Approved", None),  # an old entry without a timestamp still counts all-time
        ],
        NOW,
    )
    assert stats["U1"] == {"Approved": 2, "Rejected": 1, "This month": 2, "Last review": latest}
    assert stats["U2"] == {"Approved": 1, "Rejected": 0, "This month": 0, "Last review": None}


def test_ranks_share_place_on_ties():
    s = lambda approved, rejected: {"Approved": approved, "Rejected": rejected}  # noqa: E731
    assert lb.ranks({"A": s(10, 0), "B": s(8, 2), "C": s(5, 0), "D": s(1, 0)}) == {"A": 1, "B": 1, "C": 3, "D": 4}


class RateLimitedSlack(FakeSlack):
    def users_lookupByEmail(self, *, email):
        raise SlackApiError("ratelimited", {"ok": False, "error": "ratelimited"})


@pytest.fixture
def prod_env(monkeypatch):
    monkeypatch.setenv("FB_PROJECT_ID", "schemessg")
    monkeypatch.setenv("NOTION_LEADERBOARD_TOKEN", "t")


def test_sync_merges_email_and_slack_id_then_updates_existing_row_and_creates_new_one(prod_env):
    db = FakeFirestore()
    db.seed(
        "schemeEntries",
        "e1",
        {
            "Status": "approved",
            "approved_by": "ann@example.org",
            "approved_at": datetime(2026, 11, 5, tzinfo=timezone.utc),
        },
    )
    db.seed(
        "schemeEntries",
        "e2",
        {
            "Status": "approved",
            "approved_by": "ann@example.org",
            "approved_at": datetime(2026, 10, 20, tzinfo=timezone.utc),
        },
    )
    db.seed(
        "schemeEntries",
        "e3",
        {"Status": "rejected", "rejected_by": "U-ann", "rejected_at": datetime(2026, 11, 6, 2, tzinfo=timezone.utc)},
    )
    db.seed(
        "schemeEntries",
        "e4",
        {"Status": "approved", "approved_by": "bo@example.org", "approved_at": "2026-10-31T17:00:00Z"},
    )
    db.seed("schemeEntries", "e5", {"Status": "pending", "approved_by": "ann@example.org"})
    db.seed("schemeEntries", "e6", {"Status": "approved"})  # no reviewer recorded
    notion = FakeNotion(
        pages=[page_for("U-ann")],
        users=[
            {"id": "n-bot", "type": "bot", "bot": {}},
            {"id": "n-ann", "type": "person", "person": {"email": "Ann@Example.org"}},
        ],
    )

    result = lb.sync_review_leaderboard(db=db, notion=notion, slack=FakeSlack(), now=NOW)

    assert result == {"reviewers": 2, "reviews": 4, "created": 1, "updated": 1}
    ann, bo = (decode_row(notion.pages[page_id]) for page_id in ("page-1", "page-2"))
    assert {
        k: ann[k] for k in ("Reviewer", "Reviewer key", "Approved", "Rejected", "This month", "Rank", "Last review")
    } == {
        "Reviewer": "Ann",
        "Reviewer key": "U-ann",
        "Approved": 2,
        "Rejected": 1,
        "This month": 2,
        "Rank": 1,
        "Last review": "2026-11-06",
    }
    assert notion.pages["page-1"]["properties"]["Person"] == {"type": "people", "people": [{"id": "n-ann"}]}
    assert notion.pages["page-1"]["icon"] == {"type": "emoji", "emoji": "🥇"}
    assert {k: bo[k] for k in ("Reviewer", "Reviewer key", "Approved", "This month", "Rank", "Last review")} == {
        "Reviewer": "Bo Tan",
        "Reviewer key": "U-bo",
        "Approved": 1,
        "This month": 1,
        "Rank": 2,
        "Last review": "2026-11-01",
    }
    assert "Person" not in notion.pages["page-2"]["properties"]  # no Notion member with that email
    assert notion.pages["page-2"]["icon"] == {"type": "emoji", "emoji": "🥈"}


def test_unknown_slack_user_keeps_the_raw_value():
    directory = lb.SlackDirectory(FakeSlack())
    assert directory.resolve("U-gone") == ("U-gone", "U-gone", None)
    assert directory.resolve("gone@example.org") == ("gone@example.org", "gone@example.org", "gone@example.org")


def test_transient_slack_error_aborts_before_writing_to_notion(prod_env):
    db = FakeFirestore()
    db.seed("schemeEntries", "e1", {"Status": "approved", "approved_by": "ann@example.org", "approved_at": NOW})
    db.seed("schemeEntries", "e2", {"Status": "rejected", "rejected_by": "U-ann", "rejected_at": NOW})
    notion = FakeNotion(pages=[page_for("U-ann")])

    with pytest.raises(SlackApiError):
        lb.sync_review_leaderboard(db=db, notion=notion, slack=RateLimitedSlack(), now=NOW)
    # No email-keyed second row for Ann: nothing was written, and the scheduler's retry reruns the whole sync.
    assert notion.calls == []


@pytest.mark.parametrize(
    "project, token, expected",
    [
        ("schemessg", "real-token", "real-token"),
        ("schemessg-v3-dev", "placeholder", None),  # dev deploys the function with a placeholder secret
        ("schemessg", "", None),
    ],
)
def test_token_is_only_used_in_prod(monkeypatch, project, token, expected):
    monkeypatch.setenv("FB_PROJECT_ID", project)
    monkeypatch.setenv("NOTION_LEADERBOARD_TOKEN", token)
    assert lb.leaderboard_token() == expected


def test_sync_outside_prod_touches_nothing(monkeypatch):
    monkeypatch.setenv("FB_PROJECT_ID", "schemessg-v3-dev")
    monkeypatch.setenv("NOTION_LEADERBOARD_TOKEN", "placeholder")
    notion = FakeNotion()
    assert lb.sync_review_leaderboard(db=FakeFirestore(), notion=notion, slack=FakeSlack(), now=NOW) == {
        "skipped": "not configured"
    }
    assert notion.calls == []
