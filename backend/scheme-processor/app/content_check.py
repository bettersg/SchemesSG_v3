"""
Monthly content-change check (issue #407).

For one scheme:
1. Skip it when the weekly link check marked the link suspect or inactive, or when an earlier
   check still waits for a volunteer and is less than 2 months old.
2. Scrape the scheme link. A failed scrape adds 1 to ``content_check_fail_streak``; nothing else
   changes and the AI is not called.
3. No snapshot yet: save every page as the baseline (no diff, no AI).
4. Otherwise diff each page against its snapshot (pages matched by URL) and ask the AI reviewer
   which stored fields are now out of date. Phone/email are checked by regex instead.
5. Not flagged: the new text becomes the snapshot. Flagged: the snapshot keeps the reviewed text,
   the new text waits in ``pending_text``, and a ``contentChecks`` record holds the diff and the
   AI's suggestions for a volunteer.

Firestore:
- ``contentSnapshots/<scheme_id>/pages/<hash of page URL>``: url, text, pending_text. One doc per
  page because a whole scheme can pass Firestore's 1 MiB document limit.
- ``contentChecks/<id>``: one record per flag. No full-text copies.
- ``schemes/<id>``: last_content_checked, content_check_fail_streak (only while failing).
  ``scraped_text`` and ``last_scraped_update`` are never touched.

Prompt, filters and contact check were chosen in the trial (Notion "#407 AI reviewer test").
"""

import asyncio
import difflib
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.services.extraction import extract_contacts
from loguru import logger


SCHEMES = "schemes"
SNAPSHOTS = "contentSnapshots"
CHECKS = "contentChecks"

SKIP_STATUSES = ("inactive", "retired")
# A pending check blocks new checks for this long; after that the scheme is checked again.
PENDING_GRACE = timedelta(days=60)
# Stored diff is capped so a contentChecks record stays far below the 1 MiB document limit.
MAX_STORED_DIFF = 200_000

REVIEW_MODEL = "gpt-5.4-mini"
PROMPT_VERSION = "v3"
# Fields the reviewer sees and may update: the extractor's content fields plus regex phone/email.
CONTENT_FIELDS = (
    "llm_description",
    "summary",
    "eligibility",
    "how_to_apply",
    "agency",
    "address",
    "phone",
    "email",
    "who_is_it_for",
    "what_it_gives",
    "scheme_type",
    "service_area",
    "search_booster",
)
REGEX_FIELDS = ("phone", "email")

TRACKER_PATTERNS = ("pixel.wp.com",)  # tracking pixels change on every load
TRACKING_PARAMS = re.compile(r"^(utm_|fbclid$|gclid$)")
HTML_TAG = re.compile(r"<[a-zA-Z][^>]*>")
URLS = re.compile(r"\]\([^)]*\)|<https?://[^>]*>|https?://\S+")
IMAGES = re.compile(r"!\[[^\]]*\]\([^)]*\)")
WORDS = re.compile(r"\$?[^\W_]+(?:[.,][0-9]+)*")  # words and numbers; keeps $3,500 / 1.50 intact
CONTACT_JUNK = re.compile(r"sentry|wixpress|example\.", re.I)  # tracking-code "emails", placeholders

REVIEW_SYSTEM = """You review changes to the source web pages of a Singapore social service scheme listed on SchemesSG.

The user message gives the scheme's currently stored fields and a diff of its source pages since those fields were stored. In the diff, "Page:" names the page, lines starting with "-" were removed and lines starting with "+" were added.

Decide which stored fields are now out of date because of the changes. For each one, give the updated value, a short quote from the page text that shows the change, and the URL of the page it came from. If no stored field needs updating, return an empty list.

Only suggest a change to a field when the diff shows that a fact about this scheme has changed, or when it adds information about this scheme that the stored field lacks. Do not suggest changes for rewording or formatting, or for information about other programmes or the organisation in general.

When suggesting a change, keep the stored field's structure and wording and change only what is needed. If the stored field is empty, use your own structure.

Do not suggest changes to phone or email; those are checked separately.

The quote must be copied from an added line (starting with "+") and must show the change.

Field definitions:
{field_defs}

Return only a JSON object, no other text:
{{"changes": [{{"field": "<field name>", "new_value": <updated value>, "quote": "<short quote>", "page_url": "<page URL>"}}]}}"""

REVIEW_USER = """Scheme: {name} ({agency})

Stored fields:
{fields}

Diff:
{diff}"""


class ReviewError(Exception):
    """The AI reviewer gave no usable answer (API error, bad JSON, input too large)."""


#### Pages and diffs


def norm_url(url: str) -> str:
    """Make URLs comparable: lowercase host, drop #fragment, tracking params and trailing slash."""
    parts = urlsplit(url or "")
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not TRACKING_PARAMS.match(k)])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def page_doc_id(url: str) -> str:
    """Firestore doc IDs can't contain '/', so a page doc is named by a hash of its URL."""
    return hashlib.sha1(norm_url(url).encode()).hexdigest()


def clean_text(text: str) -> str:
    """Page text as compared month to month. HTML (Pydoll fallback) is converted to words first,
    the same way the extractor does; tracker lines are dropped."""
    if HTML_TAG.search(text or ""):
        from app.services.llm_extractor import _html_to_text

        text = _html_to_text(text)
    return "\n".join(line for line in (text or "").splitlines() if not any(t in line for t in TRACKER_PATTERNS))


def scraped_pages(scrape_result: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """{normalised URL: {url, text}}. A URL crawled twice keeps its longest copy."""
    pages: Dict[str, Dict[str, str]] = {}
    for page in scrape_result.get("pages") or []:
        text = clean_text(page.get("text") or "")
        key = norm_url(page.get("url") or "")
        if text.strip() and (key not in pages or len(text) > len(pages[key]["text"])):
            pages[key] = {"url": page["url"], "text": text}
    return pages


@dataclass
class PageDiff:
    url: str
    change: str  # "changed", "added" or "removed"
    removed: List[str]
    added: List[str]


def diff_pages(old: Dict[str, Dict[str, str]], new: Dict[str, Dict[str, str]]) -> List[PageDiff]:
    """Pages matched by normalised URL. A page only in `new` is added (all lines +), a page only
    in `old` is removed (all lines -). Unchanged pages are left out."""
    diffs = []
    for key in sorted(old.keys() | new.keys()):
        a = old[key]["text"].splitlines() if key in old else []
        b = new[key]["text"].splitlines() if key in new else []
        removed, added = [], []
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith(("---", "+++")):
                continue
            if line.startswith("-"):
                removed.append(line[1:])
            elif line.startswith("+"):
                added.append(line[1:])
        if removed or added:
            change = "added" if key not in old else "removed" if key not in new else "changed"
            diffs.append(PageDiff((new.get(key) or old[key])["url"], change, removed, added))
    return diffs


def format_diff(diffs: List[PageDiff]) -> str:
    """The diff as the reviewer reads it: "Page: <url>" then -/+ lines."""
    return "\n\n".join(
        f"Page: {d.url}\n" + "\n".join([f"-{x}" for x in d.removed] + [f"+{x}" for x in d.added]) for d in diffs
    )


#### Regex contact check


def _contacts(text: str) -> set:
    # Links and image URLs out first: IDs like .../487c6111-2149-.../ otherwise read as phone numbers.
    found = extract_contacts(URLS.sub(" ", IMAGES.sub(" ", text)), max_text_length=10**7)
    return {e.lower() for e in found.emails if not CONTACT_JUNK.search(e)} | {
        re.sub(r"\D", "", p)[-8:] for p in found.phones
    }


def contact_check(diffs: List[PageDiff], new: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    """Flag an email/phone that was on a removed line of a page present in both scrapes and is gone
    from the whole new scrape. Added contacts don't flag (extra crawled pages add many), but
    contacts added on the same page are offered as replacements."""
    everywhere = _contacts("\n".join(p["text"] for p in new.values()))
    found: Dict[str, Dict[str, Any]] = {}
    for d in diffs:
        if d.change != "changed":
            continue
        removed = _contacts("\n".join(d.removed))
        added = _contacts("\n".join(d.added)) - removed
        for contact in removed - everywhere:
            entry = found.setdefault(contact, {"contact": contact, "pages": [], "replacements": set()})
            entry["pages"].append(d.url)
            entry["replacements"] |= added
    return [{**e, "replacements": sorted(e["replacements"])} for _, e in sorted(found.items())]


#### AI reviewer


def _words(value: Any) -> str:
    text = ", ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    return " ".join(WORDS.findall(URLS.sub(" ", text).lower()))


def filter_suggestions(changes: Any, stored: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Drop phone/email (regex owns them) and copy-backs (same words as the stored value)."""
    return [
        c
        for c in (changes if isinstance(changes, list) else [])
        if isinstance(c, dict)
        and c.get("field") in CONTENT_FIELDS
        and c["field"] not in REGEX_FIELDS
        and _words(stored.get(c["field"])) != _words(c.get("new_value"))
    ]


def review_messages(scheme: Dict[str, Any], diff: str) -> List[Dict[str, str]]:
    from app.services.llm_extractor import FIELD_DEFINITIONS

    stored = {k: scheme.get(k) for k in CONTENT_FIELDS}
    user = REVIEW_USER.format(
        name=scheme.get("scheme") or "",
        agency=scheme.get("agency") or "",
        fields=json.dumps(stored, indent=2, ensure_ascii=False, default=str),
        diff=diff,
    )
    return [
        {"role": "system", "content": REVIEW_SYSTEM.format(field_defs=FIELD_DEFINITIONS)},
        {"role": "user", "content": user},
    ]


async def review_changes(scheme: Dict[str, Any], diff: str) -> List[Dict[str, Any]]:
    """Ask gpt-5.4-mini which stored fields the diff makes out of date. Returns its raw
    suggestions; raises ReviewError when there is no usable answer."""
    import litellm

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_SEA", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY_SEA", "")
    if not endpoint or not api_key:
        raise ReviewError("AZURE_OPENAI_ENDPOINT_SEA / AZURE_OPENAI_API_KEY_SEA not set")

    last_error: Optional[Exception] = None
    for attempt in range(2):  # retry once for transient errors (e.g. rate limit)
        try:
            response = await litellm.acompletion(
                model=f"azure/{REVIEW_MODEL}",
                messages=review_messages(scheme, diff),
                api_key=api_key,
                api_base=endpoint,
                api_version=os.getenv("OPENAI_API_VERSION", "2025-01-01-preview"),
                response_format={"type": "json_object"},
                reasoning_effort="low",
                max_completion_tokens=8000,
                timeout=180,
            )
            changes = json.loads(response.choices[0].message.content or "").get("changes")
            if not isinstance(changes, list):
                raise ValueError("'changes' is not a list")
            return changes
        except Exception as e:
            last_error = e
            if attempt == 0:
                logger.warning(f"Reviewer call failed, retrying: {e}")
                await asyncio.sleep(10)
    raise ReviewError(f"{type(last_error).__name__}: {last_error}"[:500])


#### Firestore


class ContentStore:
    """Firestore reads and writes for the content check. Each outcome is one batch, so a scheme is
    never left half-updated."""

    def __init__(self, db):
        self.db = db

    def get_scheme(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection(SCHEMES).document(scheme_id).get()
        return doc.to_dict() if doc.exists else None

    def latest_pending_check(self, scheme_id: str) -> Optional[datetime]:
        """created_at of the newest pending check, or None when nothing is pending."""
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = (
            self.db.collection(CHECKS)
            .where(filter=FieldFilter("scheme_id", "==", scheme_id))
            .where(filter=FieldFilter("status", "==", "pending"))
            .stream()
        )
        dates = [d.to_dict().get("created_at") for d in docs]
        return max((x for x in dates if x), default=None)

    def load_snapshot(self, scheme_id: str) -> Dict[str, Dict[str, str]]:
        pages = self.db.collection(SNAPSHOTS).document(scheme_id).collection("pages").stream()
        out = {}
        for doc in pages:
            data = doc.to_dict()
            out[norm_url(data["url"])] = {"url": data["url"], "text": data.get("text") or ""}
        return out

    def _page_ref(self, scheme_id: str, url: str):
        return self.db.collection(SNAPSHOTS).document(scheme_id).collection("pages").document(page_doc_id(url))

    def _stamp(self, batch, scheme_id: str, now: datetime):
        from firebase_admin import firestore

        batch.update(
            self.db.collection(SCHEMES).document(scheme_id),
            {"last_content_checked": now, "content_check_fail_streak": firestore.DELETE_FIELD},
        )

    def record_failure(self, scheme_id: str) -> None:
        from firebase_admin import firestore

        self.db.collection(SCHEMES).document(scheme_id).update({"content_check_fail_streak": firestore.Increment(1)})

    def save_snapshot(self, scheme_id: str, pages: Dict[str, Dict[str, str]], removed: List[str], now: datetime):
        """Baseline or not flagged: the new text becomes the reviewed text."""
        from firebase_admin import firestore

        batch = self.db.batch()
        for page in pages.values():
            batch.set(
                self._page_ref(scheme_id, page["url"]),
                {"url": page["url"], "text": page["text"], "pending_text": firestore.DELETE_FIELD, "updated_at": now},
                merge=True,
            )
        for url in removed:
            batch.delete(self._page_ref(scheme_id, url))
        self._stamp(batch, scheme_id, now)
        batch.commit()

    def save_flagged(
        self,
        scheme_id: str,
        diffs: List[PageDiff],
        new: Dict[str, Dict[str, str]],
        record: Dict[str, Any],
        now: datetime,
    ) -> str:
        """Flagged: `text` stays as reviewed; each changed page gets `pending_text` (empty for a
        removed page). A new page starts with empty `text`. Returns the contentChecks id."""
        batch = self.db.batch()
        for d in diffs:
            fields = {"url": d.url, "pending_text": new.get(norm_url(d.url), {}).get("text", ""), "updated_at": now}
            if d.change == "added":
                fields["text"] = ""
            batch.set(self._page_ref(scheme_id, d.url), fields, merge=True)
        check_ref = self.db.collection(CHECKS).document()
        batch.set(check_ref, record)
        self._stamp(batch, scheme_id, now)
        batch.commit()
        return check_ref.id


#### The check


ScrapeFn = Callable[[str], Awaitable[Dict[str, Any]]]
ReviewFn = Callable[[Dict[str, Any], str], Awaitable[List[Dict[str, Any]]]]


async def check_scheme(
    scheme_id: str,
    store: ContentStore,
    scrape: ScrapeFn,
    review: ReviewFn = review_changes,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Run the monthly check for one scheme. Returns {scheme_id, outcome, detail, check_id}, where
    outcome is one of: not_found, skipped, scrape_failed, baseline, unchanged, flagged, error."""
    now = now or datetime.now(timezone.utc)
    result: Dict[str, Any] = {"scheme_id": scheme_id, "outcome": "", "detail": None, "check_id": None}

    def done(outcome: str, detail: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Content check {scheme_id}: {outcome}{f' ({detail})' if detail else ''}")
        return {**result, "outcome": outcome, "detail": detail}

    scheme = store.get_scheme(scheme_id)
    if scheme is None:
        return done("not_found")
    if not scheme.get("link"):
        return done("skipped", "no link")
    if scheme.get("link_suspect"):
        return done("skipped", "link suspect")
    if scheme.get("status") in SKIP_STATUSES:
        return done("skipped", f"status {scheme['status']}")
    pending_since = store.latest_pending_check(scheme_id)
    if pending_since and now - pending_since < PENDING_GRACE:
        return done("skipped", f"check pending since {pending_since.date()}")

    scrape_result = await scrape(scheme["link"])
    new = scraped_pages(scrape_result)
    if scrape_result.get("error") or not new:
        store.record_failure(scheme_id)
        return done("scrape_failed", scrape_result.get("error") or "no page text")

    old = store.load_snapshot(scheme_id)
    if not old:
        store.save_snapshot(scheme_id, new, [], now)
        return done("baseline", f"{len(new)} page(s) saved")

    diffs = diff_pages(old, new)
    removed_urls = [old[k]["url"] for k in old.keys() - new.keys()]
    if not diffs:
        store.save_snapshot(scheme_id, new, removed_urls, now)
        return done("unchanged")

    diff = format_diff(diffs)
    try:
        suggestions = filter_suggestions(await review(scheme, diff), scheme)
    except ReviewError as e:
        # Nothing written: the snapshot keeps last month's text and the scheme is retried next run.
        return done("error", str(e))
    contacts = contact_check(diffs, new)

    if not suggestions and not contacts:
        store.save_snapshot(scheme_id, new, removed_urls, now)
        return done("unchanged", f"{len(diffs)} page(s) differ, nothing out of date")

    record = {
        "scheme_id": scheme_id,
        "scheme": scheme.get("scheme"),
        "link": scheme["link"],
        "status": "pending",
        "created_at": now,
        "pages": [{"url": d.url, "change": d.change} for d in diffs],
        "diff": diff[:MAX_STORED_DIFF],
        "diff_truncated": len(diff) > MAX_STORED_DIFF,
        "suggestions": suggestions,
        "contact_check": contacts,
        "model": REVIEW_MODEL,
        "prompt_version": PROMPT_VERSION,
    }
    check_id = store.save_flagged(scheme_id, diffs, new, record, now)
    result["check_id"] = check_id
    return done("flagged", f"{len(suggestions)} suggestion(s), {len(contacts)} contact(s) gone")
