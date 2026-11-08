"""Dry run of the content check: same check, no writes, report always saved."""

import asyncio
import inspect

import pytest
from app.content_check import CONTENT_TEXTS, ContentStore, page_entries, scraped_pages
from scripts.dry_run_content_check import DryRunStore, pick_sample, run


LINK = "https://example.org/aid"
READS = {"get_scheme", "get_texts"}


class Doc:
    def __init__(self, id, data):
        self.id = id
        self.exists = data is not None
        self._data = data

    def to_dict(self):
        return self._data


class Ref:
    def __init__(self, id, data):
        self.id = id
        self._data = data

    def get(self):
        return Doc(self.id, self._data)

    def update(self, *a, **k):
        raise AssertionError("dry run wrote to Firestore")

    set = update


class Collection:
    def __init__(self, docs):
        self.docs = docs

    def document(self, id=None):
        return Ref(id, self.docs.get(id))

    def list_documents(self):
        return [Ref(i, d) for i, d in self.docs.items()]

    def select(self, fields):
        return self

    def stream(self):
        return [Doc(i, d) for i, d in sorted(self.docs.items())]


class FakeDb:
    """Reads from dicts; any write fails the test."""

    def __init__(self, schemes, texts):
        self.data = {"schemes": schemes, CONTENT_TEXTS: texts}

    def collection(self, name):
        return Collection(self.data.setdefault(name, {}))

    def batch(self):
        raise AssertionError("dry run wrote to Firestore")


def hashed(text):
    new = scraped_pages({"pages": [{"url": LINK, "text": text}]})
    return page_entries(new), new


def saved_text(new):
    return {"pages": {"k": {"url": p["url"], "text": p["normalized_text"]} for p in new.values()}}


def scrape_returning(text):
    async def scrape(url):
        return {"content": "", "error": None, "pages": [{"url": url, "text": text, "main_text": ""}]}

    return scrape


def fake_ai(calls):
    async def review(scheme, pages):
        calls.append(pages)
        return [{"field": "eligibility", "new_value": "Age 65 and above", "quote": "Age 65", "page_url": LINK}]

    return review


def scheme_doc(pages=None):
    doc = {"scheme": "Aid Fund", "agency": "Example Org", "link": LINK, "eligibility": "Age 60 and above"}
    if pages is not None:
        doc["content_pages"] = pages
    return doc


@pytest.mark.parametrize("name", sorted(n for n, f in vars(ContentStore).items()
                                        if callable(f) and not n.startswith("_") and n not in READS))
def test_every_write_is_overridden_with_the_same_inputs(name):
    assert name in vars(DryRunStore), f"DryRunStore would really run ContentStore.{name}"
    real = list(inspect.signature(getattr(ContentStore, name)).parameters)
    dry = list(inspect.signature(getattr(DryRunStore, name)).parameters)
    assert dry == real


def test_unchanged_and_first_check_are_reported_without_writing():
    pages, new = hashed("Age 60 and above. Apply online.")
    db = FakeDb({"same": scheme_doc(pages), "first": scheme_doc()}, {"same": saved_text(new)})
    calls = []
    results = asyncio.run(run(db, ["same", "first"], scrape_returning("Age 60 and above. Apply online."), fake_ai(calls)))
    assert [r["outcome"] for r in results] == ["unchanged", "baseline"]
    assert calls == []


def test_changed_page_with_saved_text_reaches_the_ai():
    pages, new = hashed("Age 60 and above. Apply online.")
    db = FakeDb({"s1": scheme_doc(pages)}, {"s1": saved_text(new)})
    calls = []
    [r] = asyncio.run(run(db, ["s1"], scrape_returning("Age 65 and above. Apply online."), fake_ai(calls)))
    assert r["outcome"] == "flagged"
    assert len(calls) == 1
    assert r["pages_changed"] == [{"url": LINK, "change": "changed"}]
    assert r["suggestions"][0]["old_value"] == "Age 60 and above"


def test_empty_page_is_scrape_failed_and_the_run_carries_on():
    pages, new = hashed("Age 60 and above.")
    db = FakeDb({"a": scheme_doc(pages), "b": scheme_doc(pages)}, {"a": saved_text(new), "b": saved_text(new)})
    results = asyncio.run(run(db, ["a", "b"], scrape_returning(""), fake_ai([])))
    assert [r["outcome"] for r in results] == ["scrape_failed", "scrape_failed"]
    assert all(r["pages_changed"] == [] for r in results)


def test_sample_only_takes_schemes_with_hashes_and_saved_text():
    pages, new = hashed("Age 60 and above.")
    db = FakeDb(
        {"a": scheme_doc(pages), "b": scheme_doc(pages), "c": scheme_doc(), "d": scheme_doc(pages)},
        {"a": saved_text(new), "c": saved_text(new), "d": saved_text(new)},
    )
    assert pick_sample(db, 5) == ["a", "d"]
    assert pick_sample(db, 1) == ["a"]
