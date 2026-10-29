"""
Notion review queue for the monthly content check (issue #407).

Two jobs, both plain Notion API calls (no Notion AI):

1. Monthly push (called at the end of ``run_content_check_core``): each flagged scheme gets one
   row in the Notion review database. Fields the AI (or the contact check) says are out of date
   are pre-filled with the new value and tagged in "Changed by AI"; a ✏️ box per change in the
   row body shows the previous value and the source page. A scheme already in the queue has its
   row refreshed, unless a volunteer has already set it to Approved.
2. Hourly sweep (``scheduled_notion_content_review``): rows set to Approved or Rejected are applied
   to Firestore, recorded on their ``contentChecks`` record, then moved to Notion's trash.
   - Approved: every field in the row is written to the scheme, plus the new page hashes.
   - Rejected: only the new page hashes are saved, so the same change is not flagged again.
   - Scheme retired, or replaced through a Slack update since the push: nothing is written.
   A row whose Firestore write fails stays in Notion and is retried next hour.

Firestore stays the source of truth; Notion only holds the open review queue.
Every entry point is a no-op unless NOTION_API_TOKEN and NOTION_CONTENT_CHECK_DATA_SOURCE_ID are set.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from loguru import logger
from new_scheme.constants import SCHEME_TYPE, WHAT_IT_GIVES, WHO_IS_IT_FOR

from batch_jobs.notion_client import NotionClient, decode_row, encode_properties, rich_text


SCHEMES = "schemes"
CHECKS = "contentChecks"
RETIRED_STATUS = "retired"
# Decided records are kept this long (Firestore TTL on expires_at); pending ones never expire.
DECIDED_RETENTION = timedelta(days=183)

STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED = "Pending", "Approved", "Rejected"

# Firestore field -> plain label. The label is the "Changed by AI" tag (the ✏️ formula columns match
# on it) and the ✏️ box heading.
FIELD_LABELS = {
    "scheme": "Scheme name",
    "llm_description": "Description",
    "summary": "Summary",
    "eligibility": "Eligibility",
    "how_to_apply": "How to apply",
    "who_is_it_for": "Who is it for",
    "what_it_gives": "What it gives",
    "scheme_type": "Scheme type",
    "agency": "Agency",
    "address": "Address",
    "phone": "Phone",
    "email": "Email",
    "service_area": "Service area",
    "search_booster": "Search booster",
    "planning_area": "Planning area",
    "link": "Link",
}
COLUMN_EMOJI = {
    "llm_description": "📝",
    "summary": "💡",
    "eligibility": "🎯",
    "how_to_apply": "📋",
    "who_is_it_for": "👥",
    "what_it_gives": "🎁",
    "scheme_type": "🏷️",
    "agency": "🏢",
    "address": "📍",
    "phone": "📞",
    "email": "✉️",
    "service_area": "🌐",
    "search_booster": "🔍",
    "planning_area": "🗺️",
    "link": "🔗",
}
# Notion column -> Firestore field for every scheme field in the row. Column names (emoji included)
# are a contract with the Notion database: renaming a column in Notion makes every write to it fail.
FIELD_COLUMNS = {
    (f"{COLUMN_EMOJI[field]} {label}" if field in COLUMN_EMOJI else label): field
    for field, label in FIELD_LABELS.items()
}
FIELD_TO_COLUMN = {field: column for column, field in FIELD_COLUMNS.items()}
COLUMN_TYPES = {
    FIELD_TO_COLUMN["scheme"]: "title",
    FIELD_TO_COLUMN["who_is_it_for"]: "multi_select",
    FIELD_TO_COLUMN["what_it_gives"]: "multi_select",
    FIELD_TO_COLUMN["scheme_type"]: "multi_select",
    FIELD_TO_COLUMN["link"]: "url",
    "Status": "select",
    "Changed by AI": "multi_select",
    "Last updated": "date",
    "Scheme ID": "rich_text",
    "Check ID": "rich_text",
}
COLUMN_TYPES.update({column: "rich_text" for column in FIELD_COLUMNS if column not in COLUMN_TYPES})
# Tag fields only take these options; anything else a volunteer adds is dropped on write.
ALLOWED_OPTIONS = {
    "who_is_it_for": set(WHO_IS_IT_FOR),
    "what_it_gives": set(WHAT_IT_GIVES),
    "scheme_type": set(SCHEME_TYPE),
}
LIST_FIELDS = tuple(ALLOWED_OPTIONS)


def notion_config() -> Optional[Dict[str, str]]:
    """Return the Notion config from env, or None when this deploy must not touch Notion."""
    token = os.getenv("NOTION_API_TOKEN")
    data_source = os.getenv("NOTION_CONTENT_CHECK_DATA_SOURCE_ID")
    if not (token and data_source):
        return None
    return {"token": token, "data_source": data_source}


#### Values


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else str(value).split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def _as_text(value: Any) -> str:
    return ", ".join(_as_list(value)) if isinstance(value, (list, tuple)) else str(value or "")


def _as_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            return _as_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def allowed_tags(field: str, value: Any) -> List[str]:
    """A tag field's options that are on the allowed list (new_scheme/constants.py), in order."""
    return [option for option in _as_list(value) if option in ALLOWED_OPTIONS[field]]


def stored_value(scheme: Dict[str, Any], field: str) -> Any:
    """A scheme's current value as the review row shows it. The website shows llm_description,
    falling back to the legacy description."""
    if field == "llm_description":
        return scheme.get("llm_description") or scheme.get("description") or ""
    if field in LIST_FIELDS:
        return _as_list(scheme.get(field))
    return scheme.get(field) or ""


#### Contact check -> phone/email suggestions


def _split_contacts(value: Any) -> List[str]:
    return [part.strip() for part in re.split(r"[,;\n]", _as_text(value)) if part.strip()]


def contact_changes(scheme: Dict[str, Any], contact_check: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Turn the regex contact check into phone/email suggestions. Only a stored phone/email that is
    gone from the site changes the field: it is removed, and contacts new on the same page are
    added. Contacts are emails (lowercase) or the last 8 digits of a phone number."""
    gone = {entry["contact"] for entry in contact_check}
    added = sorted({r for entry in contact_check for r in entry.get("replacements", [])})
    sources = [page for entry in contact_check for page in entry.get("pages", [])]
    changes: Dict[str, Dict[str, Any]] = {}
    for field, is_email in (("phone", False), ("email", True)):
        key = (lambda c: c.lower()) if is_email else (lambda c: re.sub(r"\D", "", c)[-8:])
        before = _split_contacts(scheme.get(field))
        kept = [c for c in before if key(c) not in gone]
        if len(kept) == len(before):
            continue
        kept_keys = {key(c) for c in kept}
        new = kept + [c for c in added if ("@" in c) == is_email and c not in kept_keys]
        changes[field] = {"new_value": ", ".join(new), "page_url": sources[0] if sources else None}
    return changes


#### Monthly push


def suggested_changes(scheme: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """{field: {new_value, page_url}} from the AI's suggestions and the contact check."""
    changes = {
        s["field"]: {"new_value": s.get("new_value"), "page_url": s.get("page_url")}
        for s in record.get("suggestions") or []
        if s.get("field") in FIELD_TO_COLUMN
    }
    for field, change in contact_changes(scheme, record.get("contact_check") or []).items():
        changes.setdefault(field, change)
    return changes


def row_properties(
    scheme_id: str,
    check_id: str,
    scheme: Dict[str, Any],
    changes: Dict[str, Dict[str, Any]],
    today: str,
) -> Dict[str, Any]:
    """Plain row values: every field pre-filled, changed fields holding the new value."""
    values: Dict[str, Any] = {}
    for column, field in FIELD_COLUMNS.items():
        value = changes[field]["new_value"] if field in changes else stored_value(scheme, field)
        # Tag fields show only allowed options, so the row holds exactly what an approval saves.
        values[column] = allowed_tags(field, value) if field in LIST_FIELDS else _as_text(value)
    values.update(
        {
            "Status": STATUS_PENDING,
            "Changed by AI": [FIELD_LABELS[field] for field in FIELD_COLUMNS.values() if field in changes],
            "Last updated": today,
            "Scheme ID": scheme_id,
            "Check ID": check_id,
        }
    )
    return values


def _paragraph_text(label: str, value: str) -> List[dict]:
    return [{"type": "text", "text": {"content": label}, "annotations": {"bold": True}}, *rich_text(value)]


def review_blocks(
    scheme: Dict[str, Any], changes: Dict[str, Dict[str, Any]], contact_check: List[Dict[str, Any]]
) -> List[dict]:
    """Row body: a how-to note, a note for contacts gone from the site that are not in the
    phone/email fields, then one ✏️ box per changed field (new value, old value, source)."""
    blocks = [
        {
            "type": "callout",
            "callout": {
                "icon": {"type": "emoji", "emoji": "ℹ️"},
                "color": "gray_background",
                "rich_text": rich_text(
                    "Fields marked ✏️ already show the AI's new value. Compare each with its box below: to keep "
                    "the old value, copy it back into the field. Fix any other field you notice. New in the box "
                    "is what the AI suggested; if you edit the field, the field is what gets saved. Then set "
                    "Status to Approved (saves all fields) or Rejected (SchemesSG stays as it was). Text in "
                    "this section is not saved."
                ),
            },
        }
    ]
    unlisted = [e["contact"] for e in contact_check if not ({"phone", "email"} & changes.keys())]
    if unlisted:
        blocks.append(
            {
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "📞"},
                    "color": "yellow_background",
                    "rich_text": rich_text(
                        "No longer on the website: " + ", ".join(unlisted) + ". Check the phone/email fields "
                        "and the scheme's pages."
                    ),
                },
            }
        )
    for field in FIELD_COLUMNS.values():
        if field not in changes:
            continue
        new = changes[field]["new_value"]
        new = _as_text(allowed_tags(field, new) if field in LIST_FIELDS else new) or "(empty)"
        old = _as_text(stored_value(scheme, field)) or "(empty)"
        source = changes[field].get("page_url") or scheme.get("link") or ""
        blocks.append(
            {
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "✏️"},
                    "color": "yellow_background",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{FIELD_TO_COLUMN[field]}: changed by AI\n"},
                            "annotations": {"bold": True},
                        },
                        *_paragraph_text("🆕 New: ", new + "\n"),
                        *_paragraph_text("↩️ Old: ", old + "\n"),
                        {"type": "text", "text": {"content": "🔗 Source: "}, "annotations": {"bold": True}},
                        {
                            "type": "text",
                            "text": {"content": source[:2000], "link": {"url": source} if source else None},
                        },
                    ],
                },
            }
        )
    return blocks


def existing_rows(notion: NotionClient, data_source: str) -> Dict[str, Dict[str, Any]]:
    """Scheme ID -> {page_id, status, check_id} for every row in the review database."""
    rows = {}
    for page in notion.query_all(data_source):
        values = decode_row(page)
        if values.get("Scheme ID"):
            rows[values["Scheme ID"]] = {
                "page_id": page["id"],
                "status": values.get("Status"),
                "check_id": values.get("Check ID"),
            }
    return rows


def push_flagged(
    check_ids: List[str],
    db=None,
    notion: Optional[NotionClient] = None,
    cfg: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Put each flagged scheme's contentChecks record into the Notion review queue."""
    cfg = cfg or notion_config()
    if not cfg:
        logger.info("Notion review push skipped: NOTION_* not set")
        return {"skipped": "notion not configured"}
    db = db or get_firestore_client()
    notion = notion or NotionClient(cfg["token"])
    now = now or datetime.now(timezone.utc)
    counts = {"created": 0, "updated": 0, "skipped_approved": 0, "failed": 0}

    rows = existing_rows(notion, cfg["data_source"])
    for check_id in check_ids:
        try:
            record = db.collection(CHECKS).document(check_id).get().to_dict()
            if not record:
                raise ValueError(f"contentChecks/{check_id} not found")
            scheme_id = record["scheme_id"]
            scheme = db.collection(SCHEMES).document(scheme_id).get().to_dict() or {}
            changes = suggested_changes(scheme, record)
            props = encode_properties(
                row_properties(scheme_id, check_id, scheme, changes, now.date().isoformat()), COLUMN_TYPES
            )
            blocks = review_blocks(scheme, changes, record.get("contact_check") or [])
            row = rows.get(scheme_id)
            if row and row["status"] == STATUS_APPROVED:
                # The hourly sweep is about to apply it; the next monthly check catches anything newer.
                logger.warning(f"Notion row for {scheme_id} is Approved; not refreshed with check {check_id}")
                counts["skipped_approved"] += 1
                continue
            batch = db.batch()
            if row:
                notion.update_page(row["page_id"], props)
                notion.replace_children(row["page_id"], blocks)
                page_id = row["page_id"]
                if row.get("check_id") and row["check_id"] != check_id:
                    # The volunteer only ever sees the newest check, so the one it replaces is deleted.
                    batch.delete(db.collection(CHECKS).document(row["check_id"]))
                counts["updated"] += 1
            else:
                page_id = notion.create_page(cfg["data_source"], props, blocks)["id"]
                counts["created"] += 1
            batch.update(db.collection(CHECKS).document(check_id), {"notion_page_id": page_id, "pushed_at": now})
            batch.commit()
            rows[scheme_id] = {"page_id": page_id, "status": STATUS_PENDING, "check_id": check_id}
        except Exception as e:
            logger.error(f"Notion review push failed for check {check_id}: {e}")
            counts["failed"] += 1

    logger.info(f"Notion review push: {counts}")
    return counts


#### Hourly sweep


def approved_update(values: Dict[str, Any], scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Firestore fields from an Approved row. Tag fields keep only allowed options (older tags no
    longer on the list are dropped); Description goes to both llm_description and description."""
    update: Dict[str, Any] = {}
    for column, field in FIELD_COLUMNS.items():
        value = values.get(column)
        if field in LIST_FIELDS:
            update[field] = allowed_tags(field, value)
        else:
            update[field] = (value or "").strip() if isinstance(value, str) else value
    update["description"] = update["llm_description"]
    if not update.get("link"):
        update.pop("link")  # never blank the scheme link
    if not update.get("scheme"):
        update.pop("scheme")
    return update


def replaced_since_push(scheme: Dict[str, Any], record: Dict[str, Any]) -> bool:
    """True when a Slack update-in-place (dead-link replacement) was approved after the push:
    the volunteer reviewed the old site."""
    approved_at, pushed_at = _as_datetime(scheme.get("approved_at")), _as_datetime(record.get("pushed_at"))
    return bool(approved_at and pushed_at and approved_at > pushed_at)


def apply_row(db, values: Dict[str, Any], reviewer: str, now: datetime) -> Tuple[str, Optional[str]]:
    """Apply one decided row to Firestore. Returns (outcome, detail). Raises on a failed write,
    so the row stays in Notion for the next run."""
    check_id, scheme_id, status = values.get("Check ID"), values.get("Scheme ID"), values.get("Status")
    if not check_id or not scheme_id:
        raise ValueError("row has no Check ID or Scheme ID")
    check_ref = db.collection(CHECKS).document(check_id)
    record = check_ref.get().to_dict()
    if not record:
        raise ValueError(f"contentChecks/{check_id} not found")
    scheme_ref = db.collection(SCHEMES).document(scheme_id)
    scheme = scheme_ref.get().to_dict()

    if scheme is None:
        outcome, detail = "skipped", "scheme not found"
    elif scheme.get("status") == RETIRED_STATUS:
        outcome, detail = "skipped", "scheme retired"
    elif replaced_since_push(scheme, record):
        outcome, detail = "skipped", "scheme replaced in Slack after the push"
    else:
        outcome, detail = ("approved", None) if status == STATUS_APPROVED else ("rejected", None)

    decision = {
        "status": outcome,
        "decided_at": now,
        "decided_by": reviewer,
        "expires_at": now + DECIDED_RETENTION,
    }
    if detail:
        decision["skip_reason"] = detail
    if outcome == "skipped":
        check_ref.update(decision)
        return outcome, detail

    scheme_update: Dict[str, Any] = {"content_pages": record.get("new_pages") or scheme.get("content_pages") or []}
    if outcome == "approved":
        scheme_update.update(approved_update(values, scheme))
    batch = db.batch()
    batch.update(scheme_ref, scheme_update)
    batch.update(check_ref, decision)
    batch.commit()
    return outcome, detail


def sweep_decided(
    db=None,
    notion: Optional[NotionClient] = None,
    cfg: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Apply every Approved/Rejected row to Firestore, then trash the row."""
    cfg = cfg or notion_config()
    if not cfg:
        logger.info("Notion review sweep skipped: NOTION_* not set")
        return {"skipped": "notion not configured"}
    db = db or get_firestore_client()
    notion = notion or NotionClient(cfg["token"])
    now = now or datetime.now(timezone.utc)
    counts = {"approved": 0, "rejected": 0, "skipped": 0, "failed": 0}

    decided = {"or": [{"property": "Status", "select": {"equals": s}} for s in (STATUS_APPROVED, STATUS_REJECTED)]}
    for page in notion.query_all(cfg["data_source"], filter=decided):
        values = decode_row(page)
        reviewer = ", ".join(values.get("Reviewer") or []) or (page.get("last_edited_by") or {}).get("id", "")
        try:
            outcome, detail = apply_row(db, values, reviewer, now)
            notion.trash_page(page["id"])
            counts[outcome] += 1
            logger.info(f"Notion review {values.get('Scheme ID')}: {outcome}{f' ({detail})' if detail else ''}")
        except Exception as e:
            logger.error(f"Notion review sweep failed for row {page.get('id')}: {e}")
            counts["failed"] += 1

    logger.info(f"Notion review sweep: {counts}")
    return counts


@scheduler_fn.on_schedule(
    schedule="0 * * * *",  # every hour, on the hour
    region="asia-southeast1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=300,
    max_instances=1,
    retry_count=0,  # the next run is an hour away
)
def scheduled_notion_content_review(event: scheduler_fn.ScheduledEvent) -> None:
    """Apply volunteer verdicts from the Notion content review queue."""
    logger.info(f"Notion content review sweep triggered at {event.schedule_time}")
    sweep_decided()
