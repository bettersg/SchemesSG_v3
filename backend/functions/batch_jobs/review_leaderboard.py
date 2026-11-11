"""
Review Leaderboard: daily count of scheme reviews per volunteer, written to the Better.sg Notion
"Review Leaderboard" database (on the Schemes-SG "New Member Onboarding" page).

Firestore stays the source of truth. Each run recomputes all-time totals from ``schemeEntries``
(Status approved or rejected, so retirements and updates count too), so a missed or repeated run is
harmless. One Notion row per reviewer, keyed on "Reviewer key" (their Slack user ID): approvals
store the reviewer's email and rejections their Slack ID, so both are resolved through Slack and
merged. Levels, progress bars and views are Notion formulas; this job writes the counts, rank,
medal icon and, when a workspace member has the same email, the Notion "Person".

Prod only: the Better.sg workspace has no dev copy, and dev's NOTION_LEADERBOARD_TOKEN is a placeholder.
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from loguru import logger
from slack_sdk.errors import SlackApiError
from utils.catalog_filtering import as_datetime

from batch_jobs.notion_client import NotionClient, decode_row, encode_properties


ENTRIES = "schemeEntries"
PROD_PROJECT_ID = "schemessg"
# "Review Leaderboard" data source in the Better.sg workspace.
DATA_SOURCE_ID = "47fea1bd-3359-4dce-9325-620776f0a176"
SGT = timezone(timedelta(hours=8))
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
OTHER_ICON = "🎖️"

# Column name -> Notion type. Names are a contract with the Notion database; the formula columns
# (Total, Place, Level, Progress, Monthly) read these.
COLUMN_TYPES = {
    "Reviewer": "title",
    "Reviewer key": "rich_text",
    "Rank": "number",
    "Approved": "number",
    "Rejected": "number",
    "This month": "number",
    "Last review": "date",
    "Person": "people",
}

Event = Tuple[str, str, Optional[datetime]]  # (reviewer, "Approved" | "Rejected", reviewed at)


def leaderboard_token() -> Optional[str]:
    """The Notion token, or None when this deploy must not touch the Better.sg workspace."""
    token = os.getenv("NOTION_LEADERBOARD_TOKEN")
    if not token or os.getenv("FB_PROJECT_ID") != PROD_PROJECT_ID:
        return None
    return token


def review_events(db) -> List[Event]:
    """approved_by is usually an email (Slack ID when the lookup failed); rejected_by is a Slack ID."""
    events: List[Event] = []
    for status, action, by, at in (
        ("approved", "Approved", "approved_by", "approved_at"),
        ("rejected", "Rejected", "rejected_by", "rejected_at"),
    ):
        for doc in db.collection(ENTRIES).where("Status", "==", status).stream():
            data = doc.to_dict() or {}
            if data.get(by):
                events.append((data[by], action, as_datetime(data.get(at))))
    return events


def aggregate(events: Iterable[Event], now: datetime) -> Dict[str, Dict[str, Any]]:
    """Per reviewer: approvals, rejections, reviews since the 1st of this month (SGT), latest review."""
    month_start = now.astimezone(SGT).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"Approved": 0, "Rejected": 0, "This month": 0, "Last review": None}
    )
    for key, action, at in events:
        s = stats[key]
        s[action] += 1
        if at is None:
            continue
        if at >= month_start:
            s["This month"] += 1
        if s["Last review"] is None or at > s["Last review"]:
            s["Last review"] = at
    return dict(stats)


def ranks(stats: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Competition ranking by total reviews: ties share a place (1, 1, 3)."""
    totals = {key: s["Approved"] + s["Rejected"] for key, s in stats.items()}
    return {key: 1 + sum(t > totals[key] for t in totals.values()) for key in totals}


class SlackDirectory:
    """Resolves an email or Slack ID to (slack_id, display name, email).

    Falls back to the raw value only when Slack says the user doesn't exist. Any other error
    (rate limit, auth, outage) aborts the run: keying a reviewer by email for one run would split
    them into a second row that later runs never remove.
    """

    NOT_FOUND = ("users_not_found", "user_not_found")

    def __init__(self, client):
        self._client = client
        self._cache: Dict[str, Tuple[str, str, Optional[str]]] = {}

    def resolve(self, raw: str) -> Tuple[str, str, Optional[str]]:
        if raw not in self._cache:
            email = raw if "@" in raw else None
            try:
                if email:
                    user = self._client.users_lookupByEmail(email=raw)["user"]
                else:
                    user = self._client.users_info(user=raw)["user"]
                profile = user.get("profile") or {}
                name = profile.get("display_name") or user.get("real_name") or user.get("name") or raw
                self._cache[raw] = (user["id"], name, email or profile.get("email"))
            except SlackApiError as e:
                if e.response.get("error") not in self.NOT_FOUND:
                    raise
                logger.warning(f"Reviewer not found in Slack, keeping the raw value: {e}")
                self._cache[raw] = (raw, raw, email)
        return self._cache[raw]


def notion_people_by_email(notion: NotionClient) -> Dict[str, str]:
    return {
        user["person"]["email"].lower(): user["id"]
        for user in notion.list_users()
        if user.get("type") == "person" and (user.get("person") or {}).get("email")
    }


def row_properties(key: str, name: str, s: Dict[str, Any], rank: int, person_id: Optional[str]) -> dict:
    last = s["Last review"]
    values: Dict[str, Any] = {
        "Reviewer": name,
        "Reviewer key": key,
        "Rank": rank,
        "Approved": s["Approved"],
        "Rejected": s["Rejected"],
        "This month": s["This month"],
        "Last review": last.astimezone(SGT).date().isoformat() if last else None,
    }
    if person_id:  # no match: leave a Person someone set by hand
        values["Person"] = [{"id": person_id}]
    return encode_properties(values, COLUMN_TYPES)


def sync_review_leaderboard(
    db=None,
    notion: Optional[NotionClient] = None,
    slack=None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    token = leaderboard_token()  # never injectable: the prod-only check must not be bypassed
    if not token:
        logger.info("Review leaderboard sync skipped: not prod, or NOTION_LEADERBOARD_TOKEN not set")
        return {"skipped": "not configured"}
    db = db or get_firestore_client()
    notion = notion or NotionClient(token)
    if slack is None:
        from slack_integration.slack import get_slack_client

        slack = get_slack_client()
    now = now or datetime.now(timezone.utc)

    directory = SlackDirectory(slack)
    names: Dict[str, str] = {}
    emails: Dict[str, Optional[str]] = {}
    events: List[Event] = []
    for raw, action, at in review_events(db):
        key, name, email = directory.resolve(raw)
        names[key] = name
        emails[key] = emails.get(key) or email
        events.append((key, action, at))

    stats = aggregate(events, now)
    place = ranks(stats)
    people = notion_people_by_email(notion)
    rows = {decode_row(page).get("Reviewer key"): page["id"] for page in notion.query_all(DATA_SOURCE_ID)}

    created = updated = 0
    for key, s in stats.items():
        person_id = people.get((emails[key] or "").lower())
        properties = row_properties(key, names[key], s, place[key], person_id)
        icon = MEDALS.get(place[key], OTHER_ICON)
        if key in rows:
            notion.update_page(rows[key], properties, icon=icon)
            updated += 1
        else:
            notion.create_page(DATA_SOURCE_ID, properties, icon=icon)
            created += 1

    result = {"reviewers": len(stats), "reviews": len(events), "created": created, "updated": updated}
    logger.info(f"Review leaderboard synced: {result}")
    return result


@scheduler_fn.on_schedule(
    schedule="0 6 * * *",  # every morning
    timezone=scheduler_fn.Timezone("Asia/Singapore"),
    region="asia-southeast1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=540,
    max_instances=1,
    retry_count=1,  # safe: each run recomputes everything
    # Deployed: from Secret Manager, so keep it out of FUNCTIONS_ENV_VARS*.
    # Emulator: from functions/.env, after it logs that it can't read Secret Manager.
    secrets=["NOTION_LEADERBOARD_TOKEN"],
)
def scheduled_review_leaderboard_sync(event: scheduler_fn.ScheduledEvent) -> None:
    """Recount scheme reviews per volunteer and refresh the Notion Review Leaderboard (prod only)."""
    logger.info(f"Review leaderboard sync triggered at {event.schedule_time}")
    sync_review_leaderboard()
