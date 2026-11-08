"""
Notion review queue for the monthly content check (issue #407).

Two jobs, both plain Notion API calls (no Notion AI):

1. Hourly push (``push_pending``, run by ``scheduled_notion_content_review``): each record the
   monthly Cloud Run job flagged gets one row in the Notion review database. Fields the AI (or the
   contact check) says are out of date are pre-filled with the new value and tagged in "Changed by
   AI"; a ✏️ box per change in the row body shows the previous value and the source page. A scheme
   already in the queue has its row refreshed, unless a volunteer has already set it to Approved or
   Rejected. The scheme's field values at push time are saved on the record as ``pushed_values``.
2. Hourly sweep (same scheduled function, after the push): rows set to Approved or Rejected are applied
   to Firestore, recorded on their ``contentChecks`` record, then moved to Notion's trash.
   - Approved: only fields that differ from ``pushed_values`` (changed by the AI or the volunteer) are
     written, so anything else that changed the scheme since the push is kept. If Firestore also
     changed such a field, the row's value still wins and a warning is logged. A column missing from
     the row is skipped. Planning area stored as a list is saved back as a list. Records pushed
     before ``pushed_values`` existed compare against the scheme as it is now. Plus the new page hashes.
   - Rejected: only the new page hashes are saved, so the same change is not flagged again.
   - Both: last_scraped_update (the website's "Last updated") becomes the decision time, since a
     volunteer has confirmed the listing.
   - Scheme retired, or replaced through a Slack update since the push: nothing is written.
   A row whose Firestore write fails stays in Notion and is retried next hour.
   - Record already decided (an earlier run wrote it but the row was not trashed): nothing is written
     again; the row is just trashed.

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
from new_scheme.taxonomy import translate_legacy
from utils.catalog_filtering import as_datetime

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
DIFF_COLUMN = "Text Diff"
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
    DIFF_COLUMN: "rich_text",
}
COLUMN_TYPES.update({column: "rich_text" for column in FIELD_COLUMNS if column not in COLUMN_TYPES})
# Tag fields only take these options; anything else a volunteer adds is dropped on write.
TAG_OPTIONS = {"who_is_it_for": WHO_IS_IT_FOR, "what_it_gives": WHAT_IT_GIVES, "scheme_type": SCHEME_TYPE}
ALLOWED_OPTIONS = {field: set(tags) for field, tags in TAG_OPTIONS.items()}
LIST_FIELDS = tuple(ALLOWED_OPTIONS)


def notion_option(tag: str) -> str:
    """Notion option names can't contain commas, so "a, b" shows as "a / b"."""
    return tag.replace(", ", " / ").replace(",", " / ")


NOTION_TO_TAG = {notion_option(tag): tag for tags in TAG_OPTIONS.values() for tag in tags}


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


def allowed_tags(field: str, value: Any) -> List[str]:
    """A tag field's options that are on the allowed list (new_scheme/constants.py), in order.
    Accepts Firestore names or Notion's comma-free names."""
    tags = (NOTION_TO_TAG.get(option, option) for option in _as_list(value))
    return [tag for tag in tags if tag in ALLOWED_OPTIONS[field]]


def stored_value(scheme: Dict[str, Any], field: str) -> Any:
    """A scheme's current value as the review row shows it. The website shows llm_description,
    falling back to the legacy description."""
    if field == "llm_description":
        return scheme.get("llm_description") or scheme.get("description") or ""
    if field in LIST_FIELDS:
        return _as_list(scheme.get(field))
    return scheme.get(field) or ""


def field_snapshot(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """The scheme's row fields as Firestore stores them (tags untranslated), for ``pushed_values``."""
    return {
        field: stored_value(scheme, field) if field == "llm_description" else scheme.get(field)
        for field in FIELD_COLUMNS.values()
    }


def _stored_form(field: str, value: Any) -> Any:
    """A Firestore value in the form a row shows it, so it can be compared with the row: tags as a
    list, everything else as trimmed text (lists joined with ", ")."""
    return _as_list(value) if field in LIST_FIELDS else _as_text(value).strip()


def _row_form(field: str, value: Any) -> Any:
    """A row value in the form an approval saves it: allowed tags only, text trimmed."""
    return allowed_tags(field, value) if field in LIST_FIELDS else _as_text(value).strip()


#### Contact check -> phone/email suggestions


def _split_contacts(value: Any) -> List[str]:
    return [part.strip() for part in re.split(r"[,;\n]", _as_text(value)) if part.strip()]


def _phone_key(phone: str) -> str:
    """Digits used to compare phones. Must match phone_key in scheme-processor's content_check.py,
    which wrote the gone numbers: 1800/1900 numbers stay whole, a 10-digit 65... drops the 65."""
    digits = re.sub(r"\D", "", phone)
    return digits[2:] if len(digits) == 10 and digits.startswith("65") else digits


def contact_changes(scheme: Dict[str, Any], contact_check: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Turn the regex contact check into phone/email suggestions. Only a stored phone/email that is
    gone from the site changes the field: it is removed, and contacts new on the same page are
    added. Gone contacts are emails (lowercase) or a _phone_key; replacements are as the page
    writes them."""
    gone = {entry["contact"] for entry in contact_check}
    added = sorted({r for entry in contact_check for r in entry.get("replacements", [])})
    sources = [page for entry in contact_check for page in entry.get("pages", [])]
    changes: Dict[str, Dict[str, Any]] = {}
    for field, is_email in (("phone", False), ("email", True)):
        key = (lambda c: c.lower()) if is_email else _phone_key
        before = _split_contacts(scheme.get(field))
        kept = [c for c in before if key(c) not in gone]
        if len(kept) == len(before):
            continue
        kept_keys = {key(c) for c in kept}
        fresh = {key(c): c for c in added if ("@" in c) == is_email and key(c) not in kept_keys}
        new = kept + list(fresh.values())
        changes[field] = {"new_value": ", ".join(new), "page_url": sources[0] if sources else None}
    return changes


#### Monthly push


def suggested_changes(scheme: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """{field: {new_value, quote, page_url}} from the AI's suggestions and the contact check
    (which has no quote)."""
    changes = {
        s["field"]: {"new_value": s.get("new_value"), "quote": s.get("quote"), "page_url": s.get("page_url")}
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
    diff: Optional[str] = None,
) -> Dict[str, Any]:
    """Plain row values: every field pre-filled, changed fields holding the new value.
    "Last updated" is when the listing was last saved (the website's "Last updated"), so the
    review board can sort the stalest listings first."""
    listed = as_datetime(scheme.get("last_scraped_update"))
    values: Dict[str, Any] = {}
    for column, field in FIELD_COLUMNS.items():
        value = changes[field]["new_value"] if field in changes else stored_value(scheme, field)
        # Tag fields show only allowed options, so the row holds exactly what an approval saves.
        if field in LIST_FIELDS:
            values[column] = [notion_option(tag) for tag in allowed_tags(field, value)]
        else:
            values[column] = _as_text(value)
    values.update(
        {
            "Status": STATUS_PENDING,
            "Changed by AI": [FIELD_LABELS[field] for field in FIELD_COLUMNS.values() if field in changes],
            "Last updated": listed.date().isoformat() if listed else None,
            "Scheme ID": scheme_id,
            "Check ID": check_id,
            DIFF_COLUMN: _as_text(diff),
        }
    )
    return values


def _paragraph_text(label: str, value: str) -> List[dict]:
    return [{"type": "text", "text": {"content": label}, "annotations": {"bold": True}}, *rich_text(value)]


def review_blocks(
    scheme: Dict[str, Any], changes: Dict[str, Dict[str, Any]], contact_check: List[Dict[str, Any]]
) -> List[dict]:
    """Row body: a how-to note, a note for contacts gone from the site that are not in the
    phone/email fields, then one ✏️ box per changed field (new value, old value, the AI's quote
    when it gave one, source)."""
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
                    "Status to Approved (saves the fields that changed) or Rejected (SchemesSG stays as it "
                    "was). Text in this section is not saved. Only edit the values: don't rename, add or "
                    "delete columns."
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
        quote = (changes[field].get("quote") or "").strip()
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
                            "text": {"content": f"{FIELD_TO_COLUMN[field]}: changed by AI\n\n"},
                            "annotations": {"bold": True},
                        },
                        *_paragraph_text("🆕 New: ", new + "\n\n"),
                        *_paragraph_text("↩️ Old: ", old + "\n\n"),
                        *(_paragraph_text("💬 Quote: ", f'"{quote}"\n\n') if quote else []),
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


def sync_tag_options(notion: NotionClient, data_source: str) -> None:
    """Set the tag columns' dropdowns to exactly the allowed lists, so volunteers only see tags
    an approval saves. Runs at the start of every push, so taxonomy updates reach Notion."""
    properties = {
        FIELD_TO_COLUMN[field]: {"multi_select": {"options": [{"name": notion_option(tag)} for tag in tags]}}
        for field, tags in TAG_OPTIONS.items()
    }
    properties[DIFF_COLUMN] = {"rich_text": {}}
    notion.update_data_source(data_source, properties)


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
    counts = {"created": 0, "updated": 0, "skipped_decided": 0, "failed": 0}

    try:
        sync_tag_options(notion, cfg["data_source"])
    except Exception as e:
        logger.error(f"Notion tag dropdown sync failed (push continues): {e}")
    rows = existing_rows(notion, cfg["data_source"])
    for check_id in check_ids:
        try:
            record = db.collection(CHECKS).document(check_id).get().to_dict()
            if not record:
                raise ValueError(f"contentChecks/{check_id} not found")
            scheme_id = record["scheme_id"]
            scheme = db.collection(SCHEMES).document(scheme_id).get().to_dict() or {}
            # Taken before translation, so translated or dropped tags count as changed on approval.
            pushed_values = field_snapshot(scheme)
            # Old-vocabulary tags shown in today's terms (some move field); approving saves them that way.
            scheme.update(translate_legacy({field: _as_list(scheme.get(field)) for field in LIST_FIELDS}))
            changes = suggested_changes(scheme, record)
            diff = record.get("diff") if record.get("diff") is not None else record.get("text_diff")
            props = encode_properties(
                row_properties(scheme_id, check_id, scheme, changes, diff=diff),
                COLUMN_TYPES,
            )
            blocks = review_blocks(scheme, changes, record.get("contact_check") or [])
            row = rows.get(scheme_id)
            if row and row["status"] in (STATUS_APPROVED, STATUS_REJECTED):
                # The hourly sweep is about to apply the verdict; the next monthly check catches anything newer.
                logger.warning(f"Notion row for {scheme_id} is {row['status']}; not refreshed with check {check_id}")
                counts["skipped_decided"] += 1
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
            batch.update(
                db.collection(CHECKS).document(check_id),
                {"notion_page_id": page_id, "pushed_at": now, "pushed_values": pushed_values},
            )
            batch.commit()
            rows[scheme_id] = {"page_id": page_id, "status": STATUS_PENDING, "check_id": check_id}
        except Exception as e:
            logger.error(f"Notion review push failed for check {check_id}: {e}")
            counts["failed"] += 1

    logger.info(f"Notion review push: {counts}")
    return counts


#### Hourly sweep


def approved_update(
    values: Dict[str, Any], scheme: Dict[str, Any], pushed_values: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Firestore fields from an Approved row: only those that differ from ``pushed_values`` (the
    scheme at push time), i.e. changed by the AI or the volunteer. Without ``pushed_values`` (records
    pushed before it existed) the row is compared with the scheme as it is now.

    - A column missing from the row is skipped, never blanked.
    - If Firestore also changed the field since the push, the row's value wins (logged).
    - Tag fields keep only allowed options (older tags no longer on the list are dropped).
    - Planning area stored as a list is saved as a list (the row's text split on commas).
    - Description goes to both llm_description and description.
    - Scheme name and link are never blanked."""
    scheme_id = values.get("Scheme ID")
    current = field_snapshot(scheme)
    base = current if pushed_values is None else pushed_values
    update: Dict[str, Any] = {}
    for column, field in FIELD_COLUMNS.items():
        if column not in values:
            logger.warning(f"Notion review {scheme_id}: column {column!r} missing from the row; {field} not saved")
            continue
        new = _row_form(field, values[column])
        if new == _stored_form(field, base.get(field)):
            continue  # nobody changed it in Notion; keep whatever Firestore has now
        if pushed_values is not None and _stored_form(field, current[field]) != _stored_form(
            field, pushed_values.get(field)
        ):
            logger.warning(f"Notion review {scheme_id}: {field} changed in Firestore since the push; row value saved")
        update[field] = new
    if "planning_area" in update and isinstance(scheme.get("planning_area"), list):
        update["planning_area"] = [area.strip() for area in update["planning_area"].split(",") if area.strip()]
    if "llm_description" in update:
        update["description"] = update["llm_description"]
    for field in ("link", "scheme"):
        if field in update and not update[field]:
            update.pop(field)  # never blank the scheme link or name
    return update


def replaced_since_push(scheme: Dict[str, Any], record: Dict[str, Any]) -> bool:
    """True when a Slack update-in-place (dead-link replacement) was approved after the push:
    the volunteer reviewed the old site."""
    approved_at, pushed_at = as_datetime(scheme.get("approved_at")), as_datetime(record.get("pushed_at"))
    return bool(approved_at and pushed_at and approved_at > pushed_at)


def apply_row(db, values: Dict[str, Any], reviewer: str, now: datetime) -> Tuple[str, Optional[str]]:
    """Apply one decided row to Firestore. Returns (outcome, detail). Raises on a failed write,
    so the row stays in Notion for the next run. A record no longer pending was already applied by an
    earlier run whose trash step failed, so it is left as it is ("already_applied")."""
    check_id, scheme_id, status = values.get("Check ID"), values.get("Scheme ID"), values.get("Status")
    if not check_id or not scheme_id:
        raise ValueError("row has no Check ID or Scheme ID")
    check_ref = db.collection(CHECKS).document(check_id)
    record = check_ref.get().to_dict()
    if not record:
        raise ValueError(f"contentChecks/{check_id} not found")
    if record.get("status") != STATUS_PENDING.lower():
        return "already_applied", f"already {record.get('status')}"
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

    # Approved or Rejected, a volunteer has confirmed the listing, so the website's "Last updated"
    # (last_scraped_update, as a Slack approval sets it) becomes the decision time.
    scheme_update: Dict[str, Any] = {
        "content_pages": record.get("new_pages") or scheme.get("content_pages") or [],
        "last_scraped_update": now,
    }
    if outcome == "approved":
        scheme_update.update(approved_update(values, scheme, record.get("pushed_values")))
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
    counts = {"approved": 0, "rejected": 0, "skipped": 0, "already_applied": 0, "failed": 0}

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


def push_pending(
    db=None,
    notion: Optional[NotionClient] = None,
    cfg: Optional[Dict[str, str]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Find any pending contentChecks records without a Notion page and push them."""
    cfg = cfg or notion_config()
    if not cfg:
        logger.info("Notion review push skipped: NOTION_* not set")
        return {"skipped": "notion not configured"}
    db = db or get_firestore_client()
    now = now or datetime.now(timezone.utc)

    unpushed_check_ids = [
        doc.id
        # Firestore matches case-sensitively, and the monthly job saves "pending" in lowercase.
        for doc in db.collection(CHECKS).where("status", "==", STATUS_PENDING.lower()).stream()
        if not (doc.to_dict() or {}).get("notion_page_id")
    ]
    if not unpushed_check_ids:
        return {"created": 0, "updated": 0, "skipped_decided": 0, "failed": 0}

    logger.info(f"Pushing {len(unpushed_check_ids)} pending checks to Notion...")
    return push_flagged(unpushed_check_ids, db=db, notion=notion, cfg=cfg, now=now)


@scheduler_fn.on_schedule(
    schedule="0 * * * *",  # every hour, on the hour
    region="asia-southeast1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=300,
    max_instances=1,
    retry_count=0,  # the next run is an hour away
)
def scheduled_notion_content_review(event: scheduler_fn.ScheduledEvent) -> None:
    """Sync pending checks to Notion, then apply volunteer verdicts from the Notion review queue."""
    logger.info(f"Notion content review sweep triggered at {event.schedule_time}")
    push_pending()
    sweep_decided()
