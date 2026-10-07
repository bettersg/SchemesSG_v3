"""
Notion Link Queue sync (issue #443).

Mirrors every scheme that is failing its link check into the Notion "Link Queue"
database so a volunteer can record a verdict, applies those verdicts through the
existing pipelines, and appends a weekly row to the Notion "Metrics" database for
the Data Health dashboard. Firestore stays the source of truth; Notion rows are
rewritten from it, and the only writes back are verdicts:

- Moved / Retire create a ``schemeEntries`` doc, so the normal Slack review card follows.
- Checker wrong creates a link restore request; once approved, the link check stops flagging it.
- Unclear parks the row until the next weekly check.

Every entry point is a no-op unless the ``NOTION_*`` variables are set. Which
workspace a deploy syncs is decided by its token: prod uses a connection shared with
the prod root only, and dev uses a QA-only connection, so dev Firestore can never
reach the prod Notion workspace as long as the prod token stays in
``FUNCTIONS_ENV_VARS_PROD``.

Can also be run locally against a non-prod Notion copy by passing ``cfg`` and
``notion`` explicitly; see ``scripts/smoke_notion_link_queue.py``.
"""

import os
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from google.api_core.exceptions import AlreadyExists
from loguru import logger
from new_scheme.url_utils import normalize_url
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES, RETIRED_STATUS, retirement_validation_error


NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
# Notion allows ~3 requests/second per connection.
REQUEST_INTERVAL_SEC = 0.34
# Notion rejects rich text, titles and URLs longer than this.
MAX_TEXT = 2000
SOURCE = "notion-link-queue"
# Verdict -> schemeEntries typeOfRequest. Each goes through the Slack review its trigger posts.
REQUEST_TYPES = {"Moved": "update", "Retire": "retire", "Checker wrong": "restore"}

# Property name -> Notion property type. Names are a contract with the Notion
# databases: renaming a column in Notion makes every write to it fail.
LINK_QUEUE_TYPES = {
    "Scheme": "title",
    "Scheme ID": "rich_text",
    "Link": "url",
    "Agency": "rich_text",
    "Firestore status": "select",
    "Fail class": "select",
    "Status code": "number",
    "Error": "rich_text",
    "Weeks failing": "number",
    "Status reason": "rich_text",
    "Last checked": "date",
    "Verdict": "select",
    "Sync state": "select",
    "Sync message": "rich_text",
    "Entry ID": "rich_text",
    "Last synced": "date",
    # Owned by a Notion AI agent. The sync only ever clears it (see STALE_HINT).
    "AI Triage Hint": "rich_text",
}
# The AI agent re-runs on people's edits but not on API edits, so when the sync reopens or
# rejects a row the old hint ("All done…") would contradict Sync message. Clear it instead;
# it refills on the volunteer's next edit.
STALE_HINT = {"AI Triage Hint": ""}
METRICS_TYPES = {
    "Week": "title",
    "Snapshot date": "date",
    "Latest": "checkbox",
    "Total schemes": "number",
    "Searchable": "number",
    "Inactive": "number",
    "Retired": "number",
    "Suspect": "number",
    "Newly inactivated": "number",
    "Restored": "number",
    "Queue open": "number",
    "Verdicts this week": "number",
    "Submissions failed": "number",
    "Feedback total": "number",
}


def notion_config() -> Optional[Dict[str, str]]:
    """Return the Notion config from env, or None when this deploy must not touch Notion."""
    token = os.getenv("NOTION_API_TOKEN")
    link_queue = os.getenv("NOTION_LINK_QUEUE_DATA_SOURCE_ID")
    metrics = os.getenv("NOTION_METRICS_DATA_SOURCE_ID")
    if not (token and link_queue and metrics):
        return None
    return {"token": token, "link_queue": link_queue, "metrics": metrics}


class NotionClient:
    """The Notion REST calls this job needs."""

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )
        # Retry only 429s (never processed) and connection failures. read=0 so a
        # page-create POST that may have landed is never replayed into a duplicate row.
        retry = Retry(
            total=5,
            connect=2,
            read=0,
            status=5,
            status_forcelist=[429],
            allowed_methods=None,
            backoff_factor=1,
            raise_on_status=False,
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def _call(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        time.sleep(REQUEST_INTERVAL_SEC)
        response = self._session.request(method, f"{NOTION_API}{path}", json=body, timeout=30)
        if not response.ok:
            raise RuntimeError(f"Notion {method} {path} -> {response.status_code}: {response.text[:500]}")
        return response.json()

    def query_all(self, data_source_id: str) -> List[dict]:
        rows: List[dict] = []
        body: Dict[str, Any] = {"page_size": 100}
        while True:
            result = self._call("POST", f"/data_sources/{data_source_id}/query", body)
            rows.extend(result["results"])
            if not result.get("has_more"):
                return rows
            body["start_cursor"] = result["next_cursor"]

    def create_page(self, data_source_id: str, properties: dict) -> dict:
        parent = {"type": "data_source_id", "data_source_id": data_source_id}
        return self._call("POST", "/pages", {"parent": parent, "properties": properties})

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self._call("PATCH", f"/pages/{page_id}", {"properties": properties})

    def get_user(self, user_id: str) -> dict:
        return self._call("GET", f"/users/{user_id}")


def decode_property(prop: dict) -> Any:
    """Notion property value -> plain Python value."""
    kind = prop.get("type")
    value = prop.get(kind)
    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in value or [])
    if kind == "select":
        return value["name"] if value else None
    if kind == "date":
        return value["start"] if value else None
    if kind == "people":
        return [person["id"] for person in value or []]
    return value


def encode_properties(values: Dict[str, Any], types: Dict[str, str]) -> dict:
    """Plain values -> Notion property payload."""
    encoded = {}
    for name, value in values.items():
        kind = types[name]
        if kind in ("title", "rich_text"):
            encoded[name] = {kind: [{"text": {"content": value[:MAX_TEXT]}}] if value else []}
        elif kind == "select":
            encoded[name] = {"select": {"name": value} if value else None}
        elif kind == "date":
            encoded[name] = {"date": {"start": value} if value else None}
        elif kind == "url":
            encoded[name] = {"url": value[:MAX_TEXT] if value else None}
        else:
            encoded[name] = {kind: value}
    return encoded


def _decode_row(page: dict) -> Dict[str, Any]:
    return {name: decode_property(prop) for name, prop in page.get("properties", {}).items()}


def _as_datetime(value: Any) -> Optional[datetime]:
    """Firestore holds these as ISO strings (link job) or Timestamps (approval handler)."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _number(value: Any) -> Optional[int]:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def in_queue(scheme: Dict[str, Any]) -> bool:
    """The issue's queue definition: failing, suspect or inactive, and not retired."""
    status = scheme.get("status")
    if status == RETIRED_STATUS:
        return False
    return (
        (_number(scheme.get("link_check_fail_streak")) or 0) > 0
        or bool(scheme.get("link_suspect"))
        or status == "inactive"
    )


def scheme_facts(scheme_id: str, scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Backend-owned Link Queue columns, in the same shape decode_property returns."""
    checked = _as_datetime(scheme.get("last_link_check"))
    return {
        "Scheme": str(scheme.get("scheme") or scheme_id)[:MAX_TEXT],
        "Scheme ID": scheme_id,
        "Link": str(scheme.get("link") or "")[:MAX_TEXT] or None,
        "Agency": str(scheme.get("agency") or "")[:MAX_TEXT],
        # A missing status is legacy-active (see utils/reindex_embeddings.py).
        "Firestore status": scheme.get("status") or "active",
        "Fail class": scheme.get("link_check_fail_class") or None,
        "Status code": _number(scheme.get("link_check_status_code")),
        "Error": str(scheme.get("link_check_error") or "")[:MAX_TEXT],
        "Weeks failing": _number(scheme.get("link_check_fail_streak")),
        "Status reason": str(scheme.get("status_reason") or "")[:MAX_TEXT],
        # Date only: Notion normalises date-times, so a full timestamp never compares equal.
        "Last checked": checked.date().isoformat() if checked else None,
    }


def plan_row_update(row: Dict[str, Any], scheme: Optional[Dict[str, Any]], in_set: bool, now: str) -> Dict[str, Any]:
    """Return the plain column values to write for one existing Link Queue row ({} = no write)."""
    state = row.get("Sync state") or "Open"
    facts = scheme_facts(row["Scheme ID"], scheme) if scheme is not None else {}
    changed = {name: value for name, value in facts.items() if row.get(name) != value}

    def move(new_state: str, message: str, **extra: Any) -> Dict[str, Any]:
        return {**changed, **extra, "Sync state": new_state, "Sync message": message, "Last synced": now}

    if scheme is None or scheme.get("status") == RETIRED_STATUS:
        if state == "Resolved":
            return {}
        return move("Resolved", "Scheme retired" if scheme else "Scheme no longer exists")
    # Compare with the status stored on the row, so a row parked while already
    # inactive doesn't reopen on every run.
    if state == "Parked" and row.get("Firestore status") != "inactive" and facts["Firestore status"] == "inactive":
        return move("Open", "Went inactive again. Please check it again.", Verdict=None, **STALE_HINT)
    if not in_set:
        if state in ("Open", "Rejected", "Parked"):
            return move("Resolved", "Link is working again")
        # Resolved rows keep their last facts; Submitted rows wait for their outcome.
        return {} if state == "Resolved" else changed
    if state == "Resolved":
        return move("Open", "Failing the link check again", Verdict=None, **STALE_HINT)
    parked_on = (row.get("Last synced") or "")[:10]
    if state == "Parked" and facts["Last checked"] and parked_on and facts["Last checked"] > parked_on:
        return move("Open", "Still failing after this week's check. Take another look.", Verdict=None, **STALE_HINT)
    if state in ("Rejected", "Parked") and not row.get("Verdict"):
        return move("Open", "")
    return changed


def _next_entry_id(page_id: str, previous: Optional[str]) -> str:
    """notion-{page}-{n}: same n on a crash replay (Entry ID not yet saved), n+1 for a new verdict."""
    prefix = f"notion-{page_id}-"
    tail = (previous or "")[len(prefix) :] if (previous or "").startswith(prefix) else ""
    return f"{prefix}{int(tail) + 1 if tail.isdigit() else 1}"


def _verdict_error(
    row: Dict[str, Any], scheme_id: str, scheme: Dict[str, Any], schemes: Dict[str, dict]
) -> Optional[str]:
    """Plain-language reason a volunteer's verdict can't be applied yet, or None."""
    verdict = row.get("Verdict")
    if verdict == "Moved":
        new_url = (row.get("New URL") or "").strip()
        if not new_url:
            return "Paste the new web address into New URL."
        parsed = urlparse(new_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return "New URL must be a full web address starting with https://."
        if normalize_url(new_url) == normalize_url(scheme.get("link") or ""):
            return "New URL is the same as the current link."
    if verdict == "Retire":
        if not (row.get("Retire reason") or "").strip():
            return "Write in Retire reason why the scheme has ended."
        merged_into = (row.get("Merged into") or "").strip() or None
        if retirement_validation_error(
            scheme_id,
            merged_into,
            merge_target_exists=merged_into in schemes,
            merge_target_data=schemes.get(merged_into or ""),
        ):
            return "Merged into must be the Scheme ID of another scheme that is still listed."
    return None


def _submission_outcome(db, row: Dict[str, Any], schemes: Dict[str, dict], now: str) -> Optional[Dict[str, Any]]:
    """Follow a Submitted row's schemeEntries doc through the maintainer's Slack review."""
    entry_id = row.get("Entry ID")
    snapshot = db.collection("schemeEntries").document(entry_id).get() if entry_id else None
    entry = snapshot.to_dict() if snapshot is not None and snapshot.exists else None

    def reopen(message: str) -> Dict[str, Any]:
        # Clearing Verdict stops the same verdict being resubmitted every run.
        return {"Sync state": "Open", "Sync message": message, "Verdict": None, "Last synced": now, **STALE_HINT}

    if entry is None:
        return reopen("The submission was lost. Choose the verdict again.")
    if entry.get("Status") == "approved":
        message = "Approved by a maintainer"
        if entry.get("typeOfRequest") == "restore":
            message = "Approved: listed again, and searchable after Monday's reindex"
        return {"Sync state": "Resolved", "Sync message": message, "Last synced": now}
    if entry.get("Status") == "rejected":
        reason = entry.get("rejection_reason")
        return reopen(
            f"A maintainer rejected this{': ' + reason if reason else ''}. Check again and choose a verdict."
        )
    if entry.get("pipeline_status") == "duplicate":
        other_id = entry.get("duplicate_scheme_id") or ""
        other = entry.get("duplicate_scheme_name") or (schemes.get(other_id) or {}).get("scheme") or "another scheme"
        return reopen(
            f"That address already belongs to {other} ({other_id}). If it is the same scheme, "
            f"choose Retire and put {other_id} in Merged into."
        )
    if entry.get("pipeline_status") == "failed":
        return reopen("Processing failed. Choose the verdict again to retry.")
    return None  # Still waiting on the pipeline or a maintainer.


def _reviewer(
    notion: NotionClient, row: Dict[str, Any], users: Dict[str, Tuple]
) -> Tuple[Optional[str], Optional[str]]:
    """(name, email) of the person a Notion automation stamped into Verdict by."""
    ids = row.get("Verdict by") or []
    if not ids:
        return None, None
    if ids[0] not in users:
        try:
            user = notion.get_user(ids[0])
        except Exception:
            logger.exception(f"Could not look up Notion user {ids[0]}")
            user = {}
        users[ids[0]] = (user.get("name"), (user.get("person") or {}).get("email"))
    return users[ids[0]]


def push_verdict(
    db,
    notion: NotionClient,
    page_id: str,
    row: Dict[str, Any],
    scheme: Optional[Dict[str, Any]],
    schemes: Dict[str, dict],
    now: str,
    users: Dict[str, Tuple],
) -> Optional[Dict[str, Any]]:
    """Apply a volunteer's verdict, or follow a submitted one. Returns sync-column changes, or None."""
    state = row.get("Sync state") or "Open"
    verdict = row.get("Verdict")
    scheme_id = row["Scheme ID"]
    if scheme is None or scheme.get("status") == RETIRED_STATUS:
        return None  # The pull marks it Resolved; never act on a retired or missing scheme.
    if state == "Submitted":
        return _submission_outcome(db, row, schemes, now)
    if state not in ("Open", "Rejected", "Parked") or not verdict:
        return None

    def move(new_state: str, message: str, **extra: Any) -> Dict[str, Any]:
        return {**extra, "Sync state": new_state, "Sync message": message, "Last synced": now}

    if verdict == "Unclear":
        return (
            None if state == "Parked" else move("Parked", "Parked. Someone checks it again after next week's check.")
        )
    error = _verdict_error(row, scheme_id, scheme, schemes)
    if error:
        return (
            None if (state, row.get("Sync message")) == ("Rejected", error) else move("Rejected", error, **STALE_HINT)
        )

    # The same document shape update_scheme writes, so on_new_scheme_entry posts the usual
    # Slack review card. No pipeline_status, or the trigger skips it.
    name, email = _reviewer(notion, row, users)
    entry_id = _next_entry_id(page_id, row.get("Entry ID"))
    moved, retire = verdict == "Moved", verdict == "Retire"
    entry = {
        "Changes": row.get("Note") or None,
        "Description": None,
        "Link": (row.get("New URL") or "").strip() if moved else scheme.get("link"),
        "Scheme": scheme.get("scheme"),
        "Status": None,
        "entryId": None,
        "targetSchemeId": scheme_id,
        "oldLink": scheme.get("link") if moved else None,
        "retiredReason": (row.get("Retire reason") or "").strip() if retire else None,
        "mergedInto": ((row.get("Merged into") or "").strip() or None) if retire else None,
        "timestamp": datetime.now(timezone.utc),
        "userName": name,
        "userEmail": email,
        "typeOfRequest": REQUEST_TYPES[verdict],
        "source": SOURCE,
    }
    try:
        db.collection("schemeEntries").document(entry_id).create(entry)
    except AlreadyExists:
        pass  # A crash after create() last run; the entry is already in the pipeline.
    return move("Submitted", "Sent to a maintainer for approval in Slack", **{"Entry ID": entry_id})


def run_notion_link_queue_sync_core(
    db=None, *, cfg: Optional[Dict[str, str]] = None, notion: Optional[NotionClient] = None
) -> Dict[str, Any]:
    """Rewrite the Notion Link Queue from Firestore. Safe to rerun and to crash halfway."""
    cfg = cfg or notion_config()
    if not cfg:
        logger.info("Notion not configured for this project; skipping link queue sync")
        return {"skipped": True}
    db = db or get_firestore_client()
    notion = notion or NotionClient(cfg["token"])

    schemes = {doc.id: doc.to_dict() or {} for doc in db.collection("schemes").stream()}
    queue = {scheme_id for scheme_id, scheme in schemes.items() if in_queue(scheme)}
    rows = notion.query_all(cfg["link_queue"])
    now = datetime.now(timezone.utc).isoformat()
    counts: Counter = Counter()
    seen = set()
    users: Dict[str, Tuple] = {}

    for page in rows:
        row = _decode_row(page)
        scheme_id = row.get("Scheme ID")
        if not scheme_id:
            counts["skipped"] += 1
            continue
        seen.add(scheme_id)
        try:
            scheme = schemes.get(scheme_id)
            # Push before resolving: a Retire on a scheme that just stopped failing must not be lost.
            changes = push_verdict(db, notion, page["id"], row, scheme, schemes, now, users) or {}
            in_set = scheme is not None and in_queue(scheme)
            changes.update(plan_row_update({**row, **changes}, scheme, in_set, now))
            if changes:
                notion.update_page(page["id"], encode_properties(changes, LINK_QUEUE_TYPES))
                counts["updated"] += 1
        except Exception:
            logger.exception(f"Failed to sync Link Queue row for scheme {scheme_id}")
            counts["errors"] += 1

    for scheme_id in sorted(queue - seen):
        try:
            values = {**scheme_facts(scheme_id, schemes[scheme_id]), "Sync state": "Open", "Last synced": now}
            notion.create_page(cfg["link_queue"], encode_properties(values, LINK_QUEUE_TYPES))
            counts["created"] += 1
        except Exception:
            logger.exception(f"Failed to create Link Queue row for scheme {scheme_id}")
            counts["errors"] += 1

    logger.info(f"Notion link queue sync: queue set {len(queue)}, rows read {len(rows)}, {dict(counts)}")
    return {"queue": len(queue), "rows": len(rows), **counts}


def _iso_week(day: date) -> str:
    # ISO year, not calendar year: 2029-12-31 is in 2030-W01.
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def _count(items: Iterable[bool]) -> int:
    return sum(1 for item in items if item)


def append_metrics_row(
    db,
    dead_count: int,
    restored_count: int,
    *,
    cfg: Optional[Dict[str, str]] = None,
    notion: Optional[NotionClient] = None,
    today: Optional[date] = None,
) -> Optional[str]:
    """Upsert this ISO week's Metrics row and move ``Latest`` to it. Returns the page id."""
    cfg = cfg or notion_config()
    if not cfg:
        logger.info("Notion not configured for this project; skipping metrics row")
        return None
    notion = notion or NotionClient(cfg["token"])
    now = datetime.now(timezone.utc)
    today = today or now.date()
    week_ago = now - timedelta(days=7)

    def recent(value: Any) -> bool:
        moment = _as_datetime(value)
        return moment is not None and moment >= week_ago

    schemes = [doc.to_dict() or {} for doc in db.collection("schemes").stream()]
    entries = [doc.to_dict() or {} for doc in db.collection("schemeEntries").stream()]
    statuses = [scheme.get("status") for scheme in schemes]
    week = _iso_week(today)
    values = {
        "Week": week,
        "Snapshot date": today.isoformat(),
        "Latest": True,
        "Total schemes": len(schemes),
        # Same rule as reindex_embeddings: everything not inactive/retired is searchable.
        "Searchable": _count(status not in NON_SEARCHABLE_STATUSES for status in statuses),
        "Inactive": statuses.count("inactive"),
        "Retired": statuses.count(RETIRED_STATUS),
        "Suspect": _count(scheme.get("link_suspect") for scheme in schemes),
        "Newly inactivated": dead_count,
        "Restored": restored_count,
        "Queue open": _count(in_queue(scheme) for scheme in schemes),
        "Verdicts this week": _count(e.get("source") == SOURCE and recent(e.get("timestamp")) for e in entries)
        + _count(recent(scheme.get("link_check_manual_verified_at")) for scheme in schemes),
        # Cumulative: nothing resets a failed entry (see #444).
        "Submissions failed": _count(e.get("pipeline_status") == "failed" for e in entries),
        "Feedback total": len(list(db.collection("userFeedback").stream())),
    }

    rows = notion.query_all(cfg["metrics"])
    properties = encode_properties(values, METRICS_TYPES)
    existing = next((row for row in rows if _decode_row(row).get("Week") == week), None)
    if existing:
        current_id = notion.update_page(existing["id"], properties)["id"]
    else:
        current_id = notion.create_page(cfg["metrics"], properties)["id"]
    # Set Latest on the new row first; a crash here leaves two Latest rows until next week.
    for row in rows:
        if row["id"] != current_id and _decode_row(row).get("Latest"):
            notion.update_page(row["id"], encode_properties({"Latest": False}, METRICS_TYPES))
    logger.info(f"Notion metrics row {week} written")
    return current_id


@scheduler_fn.on_schedule(
    # Every 30 minutes, skipping 09:xx: the Monday link check reads every scheme at
    # 09:00 and batch-writes minutes later from that snapshot, which would overwrite
    # a verdict written in between. Keep the same (default) timezone as
    # scheduled_link_check_and_reindex, or the gap stops lining up.
    schedule="*/30 0-8,10-23 * * *",
    region="asia-southeast1",
    memory=options.MemoryOption.GB_1,
    timeout_sec=540,
    concurrency=1,
    max_instances=1,
    retry_count=0,  # The next run is 30 minutes away.
)
def scheduled_notion_link_queue_sync(event: scheduler_fn.ScheduledEvent) -> None:
    """Rewrite the Notion Link Queue from Firestore."""
    logger.info(f"Notion link queue sync triggered at {event.schedule_time}")
    run_notion_link_queue_sync_core()
