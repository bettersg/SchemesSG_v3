"""
Monthly content-change check (issue #407).

For one scheme:
1. Skip it when the weekly link check marked the link suspect or inactive, or when an earlier
check still waits for a volunteer and is less than 2 months old.
2. Scrape the scheme link. A failed scrape adds 1 to ``content_check_fail_streak``; nothing else
changes and the AI is not called.
3. Fingerprint each page: a SHA-256 hash of its main text (crawl4ai's pruning filter drops menus,
sidebars and footers), normalised to lowercase words and numbers. The phones/emails on the
full page text are kept too, because footers often hold them.
4. No hashes stored yet: save them as the baseline (no AI).
5. Otherwise a page is changed when its hash differs or its URL is new. Only changed pages go to
the AI reviewer, as full text, with the stored fields; it says which fields are now out of
date. Phone/email are checked by regex on every run, even when no hash changed.
6. Not flagged: the new hashes and contacts are saved. Flagged: the old ones stay, so the change
is found again until a volunteer acts, and a ``contentChecks`` record holds the AI's
suggestions.

Firestore:
- ``schemes/<id>``: content_pages ([{url, hash, contacts}]), last_content_checked,
content_check_fail_streak (only while failing). Normalized text is stored separately in ``schemeContent/<id>``.
``scraped_text`` and ``last_scraped_update`` are never touched.
- ``contentChecks/<id>``: one record per flag.

Prompt, filters and contact check were chosen in the trial (Notion "#407 AI reviewer test");
the prompt was adapted from reading a diff to reading whole changed pages.
"""

import asyncio
import hashlib
import difflib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.services.extraction import extract_contacts
from loguru import logger


SCHEMES = "schemes"
CHECKS = "contentChecks"
CONTENT_TEXTS = "schemeContent"
MAX_SNAPSHOT_BYTES = 900_000

SKIP_STATUSES = ("inactive", "retired")

REVIEW_MODEL = "gpt-5.4-mini"
PROMPT_VERSION = "v5-normalized-diff"
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

REVIEW_SYSTEM = """You review the source web pages of a Singapore social service scheme listed on SchemesSG.

The user message gives the scheme's currently stored fields and word-normalized diffs of changed source pages. Each page starts with "Page: <URL>". Lines beginning with + are newly added text; lines beginning with - were removed. Unmarked context is unchanged. Quotes must come from added (+) text; remove the diff marker when quoting. The text has been normalized to lowercase words and numbers.

Decide which stored fields are now out of date because of what the pages say. For each one, give the updated value, a short quote from the page text that shows the change, and the URL of the page it came from. If no stored field needs updating, return an empty list.

Only suggest a change to a field when the page text shows that a stored fact about this scheme is no longer true, or when the page gives important information about this scheme that the stored field lacks. Do not suggest changes for rewording or formatting, or for information about other programmes or the organisation in general.

When suggesting a change, keep the stored field's structure and wording and change only what is needed. If the stored field is empty, use your own structure.

Do not suggest changes to phone or email; those are checked separately.

The quote must be copied from the page text and must show the change.

Field definitions:
{field_defs}

Return only a JSON object, no other text:
{{"changes": [{{"field": "<field name>", "new_value": <updated value>, "quote": "<short quote>", "page_url": "<page URL>"}}]}}"""

REVIEW_USER = """Scheme: {name} ({agency})

Stored fields:
{fields}

Changed page diffs (with surrounding context):
{pages}"""


class ReviewError(Exception):
    """The AI reviewer gave no usable answer (API error, bad JSON, input too large)."""


#### Pages and hashes


def norm_url(url: str) -> str:
    """Make URLs comparable: lowercase host, drop #fragment, tracking params and trailing slash."""
    parts = urlsplit(url or "")
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if not TRACKING_PARAMS.match(k)])
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), query, ""))


def clean_text(text: str) -> str:
    """Page text as checked month to month. HTML (Pydoll fallback) is converted to words first,
    the same way the extractor does; tracker lines are dropped."""
    if HTML_TAG.search(text or ""):
        from app.services.llm_extractor import _html_to_text

        text = _html_to_text(text)
    return "\n".join(line for line in (text or "").splitlines() if not any(t in line for t in TRACKER_PATTERNS))


def _words(value: Any) -> str:
    """Lowercase words and numbers only: no links, punctuation, spacing or line breaks."""
    text = ", ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    return " ".join(WORDS.findall(URLS.sub(" ", text).lower()))


def page_hash(text: str) -> str:
    """Hash the exact canonical string persisted in schemeContent."""
    return hashlib.sha256(_words(text).encode("utf-8")).hexdigest()


class MainContentExtractionError(Exception):
    """An HTML page did not yield a usable main-content fingerprint."""


def scraped_pages(scrape_result: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Build canonical hashes from main text, falling back to full page text."""
    pages: Dict[str, Dict[str, Any]] = {}
    for page in scrape_result.get("pages") or []:
        url = page.get("url") or ""
        text = clean_text(page.get("text") or "")
        main = clean_text(page.get("main_text") or "")
        is_pdf = urlsplit(url).path.lower().endswith(".pdf")
        if not text.strip():
            raise MainContentExtractionError(f"Empty page text: {url}")
        if is_pdf:
            main = text
        if not _words(main):
            # Keep content elsewhere on the page when semantic/pruned extraction fails.
            # clean_text converts HTML (including the Pydoll path) to readable text.
            main = text
            logger.warning(f"Missing main content for {url}; hashing normalized full-page text")
        # A tiny semantic extraction compared with the full page may be a widget.
        # Log the anomaly, but do not reject legitimate short scheme pages.
        ratio = len(main) / max(len(text), 1)
        logger.info(f"Content extraction {url}: method={page.get('extraction_method', 'unknown')} "
                    f"full={len(text)} main={len(main)} ratio={ratio:.2f}")
        if ratio < 0.05:
            logger.warning(f"Suspiciously small main extraction: {url} ({ratio:.2%})")
        key = norm_url(url)
        if key not in pages or len(text) > len(pages[key]["text"]):
            normalized = _words(main)
            pages[key] = {"url": url, "text": text, "normalized_text": normalized,
                          "hash": page_hash(normalized)}
    return pages


def stored_pages(scheme: Dict[str, Any]) -> Optional[Dict[str, Dict[str, Any]]]:
    """{normalised URL: {url, hash, contacts}} from the scheme, or None before the baseline."""
    entries = scheme.get("content_pages")
    if not isinstance(entries, list):
        return None
    return {norm_url(e["url"]): e for e in entries if isinstance(e, dict) and e.get("url")}


def changed_pages(old: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
    """Pages whose hash differs ("changed") or whose URL is new ("added"). Pages no longer
    crawled are left out: there is no text to review."""
    return [
        {"url": new[k]["url"], "change": "added" if k not in old else "changed"}
        for k in sorted(new)
        if k not in old or old[k].get("hash") != new[k]["hash"]
    ]


def normalized_diff(old_text: str, new_text: str, context_words: int = 35) -> str:
    """Compact word-level diff with unchanged surrounding words for the AI reviewer."""
    old_words, new_words = old_text.split(), new_text.split()
    matcher = difflib.SequenceMatcher(None, old_words, new_words, autojunk=False)
    chunks = []
    for group in matcher.get_grouped_opcodes(context_words):
        lines = []
        for tag, i1, i2, j1, j2 in group:
            if tag in ("equal", "delete", "replace") and i1 != i2:
                prefix = " " if tag == "equal" else "-"
                lines.append(prefix + " ".join(old_words[i1:i2]))
            if tag in ("insert", "replace") and j1 != j2:
                lines.append("+" + " ".join(new_words[j1:j2]))
        chunks.append("\n".join(lines))
    return "\n...\n".join(chunks)


def format_pages(urls: List[str], new: Dict[str, Dict[str, Any]],
                 previous: Optional[Dict[str, str]] = None) -> str:
    """Send normalized word diffs, with surrounding context, not full page text."""
    previous = previous or {}
    sections = []
    for url in urls:
        key = norm_url(url)
        current = new[key]["normalized_text"]
        prior = previous.get(key)
        if prior is None:
            sections.append(f"Page: {url}\nNew page (no previous snapshot):\n+{current}")
        else:
            sections.append(f"Page: {url}\n{normalized_diff(prior, current)}")
    output = "\n\n".join(sections)
    return output


#### Regex contact check


def phone_key(phone: str) -> str:
    """Digits used to compare phones, so +65 6123 4567 and 6123-4567 match. 1800/1900 numbers stay
    whole. Only a 10-digit number has a country code: 6512 3456 is a local number."""
    digits = re.sub(r"\D", "", phone)
    return digits[2:] if len(digits) == 10 and digits.startswith("65") else digits


def page_contacts(text: str) -> Dict[str, str]:
    """{comparison form: form to show} for a page's contacts. Emails are lowercase in both; phones
    compare by phone_key and show as the page writes them."""
    # Links and image URLs out first: IDs like .../487c6111-2149-.../ otherwise read as phone numbers.
    found = extract_contacts(URLS.sub(" ", IMAGES.sub(" ", text)), max_text_length=10**7)
    shown = {e.lower(): e.lower() for e in found.emails if not CONTACT_JUNK.search(e)}
    for phone in found.phones_as_written:
        shown.setdefault(phone_key(phone), phone)
    return shown


def contacts(text: str) -> List[str]:
    """Emails (lowercase) and phones (phone_key) on a page, sorted."""
    return sorted(page_contacts(text))


def contact_check(old: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flag an email/phone that was on a page crawled both times and is gone from the whole new
    scrape. Added contacts don't flag (extra crawled pages add many), but contacts new on the same
    page are offered as replacements, as the page writes them."""
    new_contacts = {k: page_contacts(p["text"]) for k, p in new.items()}
    everywhere = set().union(*new_contacts.values())
    found: Dict[str, Dict[str, Any]] = {}
    for key in sorted(old.keys() & new.keys()):
        before = set(old[key].get("contacts") or [])
        for contact in before - everywhere:
            entry = found.setdefault(contact, {"contact": contact, "pages": [], "replacements": set()})
            entry["pages"].append(new[key]["url"])
            entry["replacements"] |= {shown for c, shown in new_contacts[key].items() if c not in before}
    return [{**e, "replacements": sorted(e["replacements"])} for _, e in sorted(found.items())]


def page_entries(new: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """What is stored per page on the scheme: URL, hash and contacts, no text."""
    return [{"url": p["url"], "hash": p["hash"], "contacts": contacts(p["text"])} for _, p in sorted(new.items())]


#### AI reviewer


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


def review_messages(scheme: Dict[str, Any], pages: str) -> List[Dict[str, str]]:
    from app.services.llm_extractor import FIELD_DEFINITIONS

    stored = {k: scheme.get(k) for k in CONTENT_FIELDS}
    user = REVIEW_USER.format(
        name=scheme.get("scheme") or "",
        agency=scheme.get("agency") or "",
        fields=json.dumps(stored, indent=2, ensure_ascii=False, default=str),
        pages=pages,
    )
    return [
        {"role": "system", "content": REVIEW_SYSTEM.format(field_defs=FIELD_DEFINITIONS)},
        {"role": "user", "content": user},
    ]


async def review_changes(scheme: Dict[str, Any], pages: str) -> List[Dict[str, Any]]:
    """Ask gpt-5.4-mini which stored fields the changed pages make out of date. Returns its raw
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
                messages=review_messages(scheme, pages),
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
    """Firestore reads and writes for the content check. Each outcome is one write or batch, so a
    scheme is never left half-updated."""

    def __init__(self, db):
        self.db = db

    def get_scheme(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection(SCHEMES).document(scheme_id).get()
        return doc.to_dict() if doc.exists else None

    def _stamp(self, now: datetime, **fields) -> Dict[str, Any]:
        from firebase_admin import firestore

        return {"last_content_checked": now, "content_check_fail_streak": firestore.DELETE_FIELD, **fields}

    def record_failure(self, scheme_id: str) -> None:
        from firebase_admin import firestore

        self.db.collection(SCHEMES).document(scheme_id).update({"content_check_fail_streak": firestore.Increment(1)})

    def get_texts(self, scheme_id: str) -> Optional[Dict[str, str]]:
        """Only called after hash change, or to establish missing snapshot baseline."""
        doc = self.db.collection(CONTENT_TEXTS).document(scheme_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        return {norm_url(v["url"]): v["text"] for v in data.get("pages", {}).values()
                if isinstance(v, dict) and isinstance(v.get("url"), str)
                and isinstance(v.get("text"), str)}

    def save_pages(self, scheme_id: str, pages: List[Dict[str, Any]],
                   new: Dict[str, Dict[str, Any]], now: datetime) -> None:
        """Atomically save accepted hashes and canonical text in separate documents."""
        payload = {hashlib.sha256(k.encode()).hexdigest():
                   {"url": p["url"], "text": p["normalized_text"]}
                   for k, p in sorted(new.items())}
        snapshot = {"pages": payload, "updated_at": now}
        if len(json.dumps(snapshot, ensure_ascii=False, default=str).encode("utf-8")) > MAX_SNAPSHOT_BYTES:
            raise MainContentExtractionError("Normalized snapshot exceeds Firestore document size limit")
        batch = self.db.batch()
        batch.set(self.db.collection(CONTENT_TEXTS).document(scheme_id), snapshot)
        batch.update(self.db.collection(SCHEMES).document(scheme_id),
                     self._stamp(now, content_pages=pages))
        batch.commit()

    def save_flagged(self, scheme_id: str, record: Dict[str, Any], now: datetime) -> str:
        """Flagged: the stored hashes stay as they are. Returns the contentChecks id."""
        batch = self.db.batch()
        check_ref = self.db.collection(CHECKS).document()
        batch.set(check_ref, record)
        batch.update(self.db.collection(SCHEMES).document(scheme_id), self._stamp(now))
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
    """Run a content check for one scheme. Returns {scheme_id, outcome, detail, check_id}, where
    outcome is one of: not_found, skipped, scrape_failed, baseline, unchanged, flagged, error."""
    now = now or datetime.now(timezone.utc)
    result: Dict[str, Any] = {"scheme_id": scheme_id, "outcome": "", "detail": None, "check_id": None, "diff": None}

    def done(outcome: str, detail: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Content check {scheme_id}: {outcome}{f' ({detail})' if detail else ''}")
        return {**result, "outcome": outcome, "detail": detail}

    scheme = store.get_scheme(scheme_id)
    if scheme is None:
        return done("not_found")
    result["scheme_name"] = scheme.get("scheme")
    if not scheme.get("link"):
        return done("skipped", "no link")
    if scheme.get("link_suspect"):
        return done("skipped", "link suspect")
    if scheme.get("status") in SKIP_STATUSES:
        return done("skipped", f"status {scheme['status']}")
    # One scrape only; missing main content falls back to normalized full-page text.
    try:
        scrape_result = await scrape(scheme["link"])
        if scrape_result.get("error"):
            raise MainContentExtractionError(str(scrape_result["error"]))
        new = scraped_pages(scrape_result)
        if not new:
            raise MainContentExtractionError("No pages extracted")
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        logger.warning(f"Content scrape failed for {scheme['link']}: {reason}")
        store.record_failure(scheme_id)
        return done("scrape_failed", reason[:500])

    old = stored_pages(scheme)
    if old is None:
        store.save_pages(scheme_id, page_entries(new), new, now)
        return done("baseline", f"{len(new)} page(s) saved")

    changed = changed_pages(old, new)
    # Existing hashes without text are a migration baseline, not an AI-reviewable diff.
    # During the requested full rebaseline, reset schemes without a snapshot.
    previous = None
    if changed:
        previous = store.get_texts(scheme_id)
        if previous is None or any(
            c["change"] == "changed" and norm_url(c["url"]) not in previous
            for c in changed
        ):
            store.save_pages(scheme_id, page_entries(new), new, now)
            return done("baseline", "normalized text snapshot initialized")
    contacts_gone = contact_check(old, new)
    if not changed and not contacts_gone:
        store.save_pages(scheme_id, page_entries(new), new, now)
        return done("unchanged")

    suggestions: List[Dict[str, Any]] = []
    cut = False
    text_diff = None
    if changed:
        pages = format_pages([c["url"] for c in changed], new, previous or {})
        text_diff = pages if pages.strip() else None
        try:
            suggestions = filter_suggestions(await review(scheme, pages), scheme)
        except ReviewError as e:
            # Nothing written: the stored hashes stay and the scheme is retried next run.
            return done("error", str(e))

    if not suggestions and not contacts_gone:
        store.save_pages(scheme_id, page_entries(new), new, now)
        return done("unchanged", f"{len(changed)} page(s) changed, nothing out of date")

    record = {
        "scheme_id": scheme_id,
        "scheme": scheme.get("scheme"),
        "link": scheme["link"],
        "status": "pending",
        "created_at": now,
        "pages": changed,
        "diff": text_diff,
        "text_diff": text_diff,
        "review_input_truncated": cut,
        "suggestions": suggestions,
        "contact_check": contacts_gone,
        "new_pages": page_entries(new),
        "model": REVIEW_MODEL,
        "prompt_version": PROMPT_VERSION,
    }
    check_id = store.save_flagged(scheme_id, record, now)
    result["check_id"] = check_id
    result["diff"] = text_diff
    return done("flagged", f"{len(suggestions)} suggestion(s), {len(contacts_gone)} contact(s) gone")
