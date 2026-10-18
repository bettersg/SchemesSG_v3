"""Unit tests for the monthly content-change check (app/content_check.py).

Firestore, the scraper and the AI reviewer are replaced by in-memory fakes.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from app.content_check import (
    ReviewError,
    check_scheme,
    contact_check,
    diff_pages,
    filter_suggestions,
    format_diff,
    norm_url,
    page_doc_id,
    scraped_pages,
)


NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)
LINK = "https://example.org/aid"


class FakeStore:
    """Same methods as ContentStore, backed by dicts."""

    def __init__(self, scheme=None, snapshot=None, pending_since=None):
        self.scheme = scheme
        self.snapshot = {norm_url(u): {"url": u, "text": t} for u, t in (snapshot or {}).items()}
        self.pending_since = pending_since
        self.fail_streak = 0
        self.stamped = None
        self.pending = {}
        self.records = []

    def get_scheme(self, scheme_id):
        return self.scheme

    def latest_pending_check(self, scheme_id):
        return self.pending_since

    def load_snapshot(self, scheme_id):
        return dict(self.snapshot)

    def record_failure(self, scheme_id):
        self.fail_streak += 1

    def save_snapshot(self, scheme_id, pages, removed, now):
        self.snapshot.update({norm_url(p["url"]): dict(p) for p in pages.values()})
        for url in removed:
            self.snapshot.pop(norm_url(url))
        self.stamped = now

    def save_flagged(self, scheme_id, diffs, new, record, now):
        for d in diffs:
            self.pending[d.url] = new.get(norm_url(d.url), {}).get("text", "")
        self.records.append(record)
        self.stamped = now
        return "check-1"


def scheme(**extra):
    return {"scheme": "Aid Fund", "agency": "Example Org", "link": LINK, "eligibility": "Age 60 and above", **extra}


def scraper(pages=None, error=None):
    async def scrape(url):
        return {"content": "", "error": error, "pages": [{"url": u, "text": t} for u, t in (pages or {}).items()]}

    return scrape


def reviewer(changes=None, error=None):
    calls = []

    async def review(scheme, diff):
        calls.append(diff)
        if error:
            raise ReviewError(error)
        return changes or []

    review.calls = calls
    return review


def run(store, scrape=None, review=None):
    return asyncio.run(check_scheme("s1", store, scrape or scraper({LINK: "x"}), review or reviewer(), now=NOW))


#### Skips


@pytest.mark.parametrize(
    "fields, detail",
    [
        ({"link_suspect": True}, "link suspect"),
        ({"status": "inactive"}, "status inactive"),
        ({"status": "retired"}, "status retired"),
        ({"link": ""}, "no link"),
    ],
)
def test_skips_without_scraping(fields, detail):
    store = FakeStore(scheme(**fields))
    result = run(store, scrape=scraper(error="should not scrape"))
    assert (result["outcome"], result["detail"]) == ("skipped", detail)
    assert store.fail_streak == 0 and store.stamped is None


def test_pending_check_under_two_months_skips():
    store = FakeStore(scheme(), {LINK: "old"}, pending_since=NOW - timedelta(days=30))
    assert run(store)["outcome"] == "skipped"


def test_pending_check_over_two_months_is_checked_again():
    store = FakeStore(scheme(), {LINK: "old"}, pending_since=NOW - timedelta(days=61))
    assert run(store, scrape=scraper({LINK: "old"}))["outcome"] == "unchanged"


def test_missing_scheme():
    assert run(FakeStore(None))["outcome"] == "not_found"


#### Scrape failure and baseline


def test_failed_scrape_counts_and_leaves_snapshot():
    store = FakeStore(scheme(), {LINK: "old"})
    review = reviewer()
    result = run(store, scrape=scraper(error="MANUAL_REVIEW_NEEDED: Cloudflare"), review=review)
    assert result["outcome"] == "scrape_failed"
    assert store.fail_streak == 1
    assert store.snapshot[norm_url(LINK)]["text"] == "old"
    assert store.stamped is None and review.calls == []


def test_blank_scrape_counts_as_failed():
    store = FakeStore(scheme())
    assert run(store, scrape=scraper({LINK: "  \n"}))["outcome"] == "scrape_failed"
    assert store.fail_streak == 1


def test_first_check_saves_baseline_without_ai():
    store = FakeStore(scheme())
    review = reviewer()
    result = run(store, scrape=scraper({LINK: "a", LINK + "/apply": "b"}), review=review)
    assert result["outcome"] == "baseline"
    assert len(store.snapshot) == 2 and store.stamped == NOW
    assert review.calls == []


#### Compare


def test_identical_scrape_skips_ai():
    store = FakeStore(scheme(), {LINK: "same"})
    review = reviewer()
    assert run(store, scrape=scraper({LINK: "same"}), review=review)["outcome"] == "unchanged"
    assert review.calls == [] and store.stamped == NOW


def test_not_flagged_overwrites_snapshot():
    store = FakeStore(scheme(), {LINK: "Opening hours 9am", LINK + "/news": "old news"})
    result = run(store, scrape=scraper({LINK: "Opening hours 10am"}), review=reviewer([]))
    assert result["outcome"] == "unchanged"
    assert store.snapshot == {norm_url(LINK): {"url": LINK, "text": "Opening hours 10am"}}  # /news removed


def test_flagged_keeps_text_and_saves_pending():
    store = FakeStore(scheme(), {LINK: "Age 60 and above"})
    change = {"field": "eligibility", "new_value": "Age 65 and above", "quote": "Age 65", "page_url": LINK}
    result = run(store, scrape=scraper({LINK: "Age 65 and above"}), review=reviewer([change]))
    assert (result["outcome"], result["check_id"]) == ("flagged", "check-1")
    assert store.snapshot[norm_url(LINK)]["text"] == "Age 60 and above"
    assert store.pending == {LINK: "Age 65 and above"}
    record = store.records[0]
    assert record["status"] == "pending" and record["suggestions"] == [change]
    assert record["diff"] == f"Page: {LINK}\n-Age 60 and above\n+Age 65 and above"


def test_review_error_writes_nothing():
    store = FakeStore(scheme(), {LINK: "old"})
    result = run(store, scrape=scraper({LINK: "new"}), review=reviewer(error="RateLimitError"))
    assert result["outcome"] == "error"
    assert store.stamped is None and store.snapshot[norm_url(LINK)]["text"] == "old"


def test_removed_contact_flags_even_without_ai_suggestion():
    store = FakeStore(scheme(), {LINK: "Call 6123 4567 for help"})
    result = run(store, scrape=scraper({LINK: "Call 6999 8888 for help"}), review=reviewer([]))
    assert result["outcome"] == "flagged"
    assert store.records[0]["contact_check"] == [
        {"contact": "61234567", "pages": [LINK], "replacements": ["69998888"]}
    ]


#### Helpers


def test_pages_matched_by_url_not_order():
    old = {norm_url(u): {"url": u, "text": t} for u, t in {LINK: "a", LINK + "/b": "b"}.items()}
    new = {norm_url(u): {"url": u, "text": t} for u, t in {LINK + "/b/": "b", LINK + "?utm_source=x": "a"}.items()}
    assert diff_pages(old, new) == []


def test_added_and_removed_pages():
    old = {norm_url(LINK + "/old"): {"url": LINK + "/old", "text": "gone line"}}
    new = {norm_url(LINK + "/new"): {"url": LINK + "/new", "text": "new line"}}
    diffs = diff_pages(old, new)
    assert [(d.url, d.change) for d in diffs] == [(LINK + "/new", "added"), (LINK + "/old", "removed")]
    assert format_diff(diffs) == f"Page: {LINK}/new\n+new line\n\nPage: {LINK}/old\n-gone line"


def test_scraped_pages_drops_trackers_and_keeps_longest_copy():
    pages = scraped_pages(
        {
            "pages": [
                {"url": LINK, "text": "short"},
                {"url": LINK + "/", "text": "longer\n![](https://pixel.wp.com/g.gif?rand=1)"},
            ]
        }
    )
    assert pages == {norm_url(LINK): {"url": LINK + "/", "text": "longer"}}


def test_scraped_pages_converts_html():
    pages = scraped_pages(
        {"pages": [{"url": LINK, "text": "<html><body><script>x()</script><p>Hello</p></body></html>"}]}
    )
    assert pages[norm_url(LINK)]["text"] == "Hello"


def test_filter_drops_contacts_copy_backs_and_unknown_fields():
    stored = {"eligibility": "Age 60 and above.", "summary": "Helps seniors"}
    changes = [
        {"field": "phone", "new_value": "6999 8888"},
        {"field": "eligibility", "new_value": "age 60 and above"},  # same words: copy-back
        {"field": "not_a_field", "new_value": "x"},
        "not a dict",
        {"field": "summary", "new_value": "Helps seniors and caregivers"},
    ]
    assert filter_suggestions(changes, stored) == [changes[-1]]


def test_contact_in_link_is_not_a_phone_number():
    old = {norm_url(LINK): {"url": LINK, "text": "![logo](https://cdn.example.org/487c6111-2149-abcd/logo.png)"}}
    new = {norm_url(LINK): {"url": LINK, "text": "![logo](https://cdn.example.org/ffff0000-1111-abcd/logo.png)"}}
    assert contact_check(diff_pages(old, new), new) == []


def test_page_doc_id_is_stable_and_firestore_safe():
    assert page_doc_id(LINK + "/") == page_doc_id(LINK + "#top")
    assert "/" not in page_doc_id(LINK)
