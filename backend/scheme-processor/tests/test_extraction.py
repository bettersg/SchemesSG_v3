"""Unit tests for app/services/extraction.py."""

from app.services.extraction import extract_contacts, select_best_logo


def test_extract_contacts_keeps_the_written_form_and_leaves_phones_unchanged():
    found = extract_contacts("Call 1800 123 4567 or 6765-4321, again 6765-4321")
    assert found.phones == ["67654321", "18001234567"]
    assert found.phones_as_written == ["6765-4321", "1800 123 4567"]


def test_extract_contacts_tidies_a_number_split_over_a_line():
    assert extract_contacts("Call 6765\n4321").phones_as_written == ["6765 4321"]


def test_select_best_logo_handles_none_fields():
    # crawl4ai returns desc=None (and sometimes alt=None); this used to crash,
    # which the scraper mistook for a Cloudflare block.
    images = [
        {"src": "https://example.org/logo.svg", "alt": None, "desc": None, "score": 1},
        {"src": None, "alt": "photo", "desc": None, "score": 5},
    ]
    assert select_best_logo(images, validate=False) == "https://example.org/logo.svg"
