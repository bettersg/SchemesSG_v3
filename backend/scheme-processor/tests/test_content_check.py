"""Unit tests for the monthly content-change check (app/content_check.py).

Firestore, the scraper and the AI reviewer are replaced by in-memory fakes.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from app.content_check import (
    MAX_REVIEW_CHARS,
    ReviewError,
    changed_pages,
    check_scheme,
    contact_check,
    filter_suggestions,
    format_pages,
    norm_url,
    page_entries,
    page_hash,
    scraped_pages,
)


NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)
LINK = "https://example.org/aid"


class FakeStore:
    """Same methods as ContentStore, backed by dicts."""

    def __init__(self, scheme=None, pending_since=None):
        self.scheme = scheme
        self.pending_since = pending_since
        self.fail_streak = 0
        self.stamped = None
        self.records = []

    def get_scheme(self, scheme_id):
        return self.scheme

    def latest_pending_check(self, scheme_id):
        return self.pending_since

    def record_failure(self, scheme_id):
        self.fail_streak += 1

    def save_pages(self, scheme_id, pages, now):
        self.scheme["content_pages"] = pages
        self.stamped = now

    def save_flagged(self, scheme_id, record, now):
        self.records.append(record)
        self.stamped = now
        return "check-1"


def baseline(pages):
    """content_pages as a baseline run would have stored them for {url: text}."""
    return page_entries(scraped_pages({"pages": [{"url": u, "text": t} for u, t in pages.items()]}))


def scheme(old_pages=None, **extra):
    fields = {"scheme": "Aid Fund", "agency": "Example Org", "link": LINK, "eligibility": "Age 60 and above"}
    if old_pages is not None:
        fields["content_pages"] = baseline(old_pages)
    return {**fields, **extra}


def scraper(pages=None, error=None, main=None):
    """pages: {url: full text}; main: {url: pruned main text}."""

    async def scrape(url):
        return {
            "content": "",
            "error": error,
            "pages": [{"url": u, "text": t, "main_text": (main or {}).get(u, "")} for u, t in (pages or {}).items()],
        }

    return scrape


def reviewer(changes=None, error=None):
    calls = []

    async def review(scheme, pages):
        calls.append(pages)
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
    store = FakeStore(scheme({LINK: "old"}), pending_since=NOW - timedelta(days=30))
    assert run(store)["outcome"] == "skipped"


def test_pending_check_over_two_months_is_checked_again():
    store = FakeStore(scheme({LINK: "old"}), pending_since=NOW - timedelta(days=61))
    assert run(store, scrape=scraper({LINK: "old"}))["outcome"] == "unchanged"


def test_missing_scheme():
    assert run(FakeStore(None))["outcome"] == "not_found"


#### Scrape failure and baseline


def test_failed_scrape_counts_and_leaves_hashes():
    store = FakeStore(scheme({LINK: "old"}))
    before = list(store.scheme["content_pages"])
    review = reviewer()
    result = run(store, scrape=scraper(error="MANUAL_REVIEW_NEEDED: Cloudflare"), review=review)
    assert result["outcome"] == "scrape_failed"
    assert store.fail_streak == 1
    assert store.scheme["content_pages"] == before
    assert store.stamped is None and review.calls == []


def test_blank_scrape_counts_as_failed():
    store = FakeStore(scheme())
    assert run(store, scrape=scraper({LINK: "  \n"}))["outcome"] == "scrape_failed"
    assert store.fail_streak == 1


def test_first_check_saves_hashes_and_contacts_without_ai():
    store = FakeStore(scheme())
    review = reviewer()
    result = run(store, scrape=scraper({LINK: "Call 6123 4567", LINK + "/apply": "b"}), review=review)
    assert result["outcome"] == "baseline"
    assert store.scheme["content_pages"] == [
        {"url": LINK, "hash": page_hash("Call 6123 4567"), "contacts": ["61234567"]},
        {"url": LINK + "/apply", "hash": page_hash("b"), "contacts": []},
    ]
    assert "text" not in store.scheme["content_pages"][0]
    assert store.stamped == NOW and review.calls == []


#### Compare


def test_same_hashes_skip_ai():
    store = FakeStore(scheme({LINK: "same"}))
    review = reviewer()
    assert run(store, scrape=scraper({LINK: "same"}), review=review)["outcome"] == "unchanged"
    assert review.calls == [] and store.stamped == NOW


def test_formatting_only_change_keeps_hash():
    store = FakeStore(scheme({LINK: "Opening hours: 9am, Mon-Fri"}))
    review = reviewer()
    result = run(store, scrape=scraper({LINK: "**opening hours** 9am\n\nmon fri"}), review=review)
    assert result["outcome"] == "unchanged" and review.calls == []


def test_hash_uses_main_text_so_footer_noise_is_ignored():
    store = FakeStore(scheme())
    run(store, scrape=scraper({LINK: "Main\nFooter (c) 2026"}, main={LINK: "Main"}))
    review = reviewer()
    result = run(store, scrape=scraper({LINK: "Main\nFooter (c) 2027"}, main={LINK: "Main"}), review=review)
    assert result["outcome"] == "unchanged" and review.calls == []


def test_only_changed_pages_go_to_ai_as_full_text():
    store = FakeStore(scheme({LINK: "Age 60 and above", LINK + "/about": "About us"}))
    review = reviewer([])
    run(store, scrape=scraper({LINK: "Age 65 and above\nFooter", LINK + "/about": "About us"}), review=review)
    assert review.calls == [f"Page: {LINK}\nAge 65 and above\nFooter"]


def test_not_flagged_saves_new_hashes():
    store = FakeStore(scheme({LINK: "Opening hours 9am", LINK + "/news": "old news"}))
    result = run(store, scrape=scraper({LINK: "Opening hours 10am"}), review=reviewer([]))
    assert result["outcome"] == "unchanged"
    assert store.scheme["content_pages"] == baseline({LINK: "Opening hours 10am"})  # /news dropped


def test_flagged_keeps_old_hashes_and_writes_record():
    store = FakeStore(scheme({LINK: "Age 60 and above"}))
    before = list(store.scheme["content_pages"])
    change = {"field": "eligibility", "new_value": "Age 65 and above", "quote": "Age 65", "page_url": LINK}
    result = run(store, scrape=scraper({LINK: "Age 65 and above"}), review=reviewer([change]))
    assert (result["outcome"], result["check_id"]) == ("flagged", "check-1")
    assert store.scheme["content_pages"] == before
    record = store.records[0]
    assert record["status"] == "pending" and record["suggestions"] == [change]
    assert record["pages"] == [{"url": LINK, "change": "changed"}]
    assert record["review_input_truncated"] is False


def test_review_error_writes_nothing():
    store = FakeStore(scheme({LINK: "old"}))
    before = list(store.scheme["content_pages"])
    result = run(store, scrape=scraper({LINK: "new"}), review=reviewer(error="RateLimitError"))
    assert result["outcome"] == "error"
    assert store.stamped is None and store.scheme["content_pages"] == before


def test_removed_contact_flags_even_without_ai_suggestion():
    store = FakeStore(scheme({LINK: "Call 6123 4567 for help"}))
    result = run(store, scrape=scraper({LINK: "Call 6999 8888 for help"}), review=reviewer([]))
    assert result["outcome"] == "flagged"
    assert store.records[0]["contact_check"] == [
        {"contact": "61234567", "pages": [LINK], "replacements": ["69998888"]}
    ]


def test_footer_contact_change_flags_when_main_text_hash_is_same():
    store = FakeStore(scheme())
    run(store, scrape=scraper({LINK: "Main\nCall 6123 4567"}, main={LINK: "Main"}))
    review = reviewer()
    result = run(store, scrape=scraper({LINK: "Main\nCall 6999 8888"}, main={LINK: "Main"}), review=review)
    assert result["outcome"] == "flagged" and review.calls == []
    assert store.records[0]["pages"] == []
    assert store.records[0]["contact_check"][0]["contact"] == "61234567"


#### Helpers


def test_pages_matched_by_url_not_order():
    old = {norm_url(e["url"]): e for e in baseline({LINK: "a", LINK + "/b": "b"})}
    new = scraped_pages({"pages": [{"url": LINK + "/b/", "text": "b"}, {"url": LINK + "?utm_source=x", "text": "a"}]})
    assert changed_pages(old, new) == []


def test_added_page_is_changed_and_removed_page_is_not():
    old = {norm_url(e["url"]): e for e in baseline({LINK + "/old": "gone"})}
    new = scraped_pages({"pages": [{"url": LINK + "/new", "text": "new"}]})
    assert changed_pages(old, new) == [{"url": LINK + "/new", "change": "added"}]


def test_hash_keeps_numbers_intact():
    assert page_hash("Grant: $3,500") != page_hash("Grant: $35.00")
    assert page_hash("Grant: $3,500") == page_hash("grant $3,500")


def test_review_input_is_capped():
    new = scraped_pages({"pages": [{"url": LINK, "text": "x" * (MAX_REVIEW_CHARS + 10)}]})
    text, cut = format_pages([LINK], new)
    assert len(text) == MAX_REVIEW_CHARS and cut


def test_scraped_pages_drops_trackers_and_keeps_longest_copy():
    pages = scraped_pages(
        {
            "pages": [
                {"url": LINK, "text": "short"},
                {"url": LINK + "/", "text": "longer\n![](https://pixel.wp.com/g.gif?rand=1)"},
            ]
        }
    )
    assert pages == {norm_url(LINK): {"url": LINK + "/", "text": "longer", "hash": page_hash("longer")}}


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
    old = {
        norm_url(e["url"]): e for e in baseline({LINK: "![logo](https://cdn.example.org/487c6111-2149-abcd/logo.png)"})
    }
    new = scraped_pages(
        {"pages": [{"url": LINK, "text": "![logo](https://cdn.example.org/ffff0000-1111-abcd/logo.png)"}]}
    )
    assert old[norm_url(LINK)]["contacts"] == []
    assert contact_check(old, new) == []
