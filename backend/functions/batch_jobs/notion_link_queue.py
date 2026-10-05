"""
Notion Link Queue sync (issue #443).

Mirrors every scheme that is failing its link check into the Notion "Link Queue"
database so a volunteer can record a verdict, and appends a weekly row to the
Notion "Metrics" database for the Data Health dashboard. Firestore stays the
source of truth; Notion rows are rewritten from it.

Notion covers production only. Every entry point is a no-op unless the
``NOTION_*`` variables are set *and* ``FB_PROJECT_ID`` is the prod project, so a
dev deploy (or a local ``.env`` with dev creds) never mixes dev Firestore with
the prod Notion workspace.

Can also be run locally against a non-prod Notion copy by passing ``cfg`` and
``notion`` explicitly; see ``scripts/smoke_notion_link_queue.py``.
"""

import os
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests
from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES, RETIRED_STATUS


PROD_PROJECT_ID = "schemessg"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
# Notion allows ~3 requests/second per connection.
REQUEST_INTERVAL_SEC = 0.34
# Notion rejects rich text, titles and URLs longer than this.
MAX_TEXT = 2000
SOURCE = "notion-link-queue"

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
}
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
    if os.getenv("FB_PROJECT_ID") != PROD_PROJECT_ID:
        logger.warning("NOTION_* is set outside the prod project; refusing to sync Notion")
        return None
    return {"token": token, "link_queue": link_queue, "metrics": metrics}


class NotionClient:
    """The four Notion REST calls this job needs."""

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
    if in_set:
        if state == "Resolved":
            return move("Open", "Failing the link check again", Verdict=None)
        return changed
    if state in ("Open", "Rejected", "Parked"):
        return move("Resolved", "Link is working again")
    # Resolved rows keep their last facts; Submitted/Applied rows wait for their outcome.
    return {} if state == "Resolved" else changed


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

    for page in rows:
        row = _decode_row(page)
        scheme_id = row.get("Scheme ID")
        if not scheme_id:
            counts["skipped"] += 1
            continue
        seen.add(scheme_id)
        try:
            changes = plan_row_update(row, schemes.get(scheme_id), scheme_id in queue, now)
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
    """Rewrite the Notion Link Queue from Firestore (prod only)."""
    logger.info(f"Notion link queue sync triggered at {event.schedule_time}")
    run_notion_link_queue_sync_core()
