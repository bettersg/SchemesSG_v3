"""Unit tests for app/services/extraction.py."""

from app.services.extraction import select_best_logo


def test_select_best_logo_handles_none_fields():
    # crawl4ai returns desc=None (and sometimes alt=None); this used to crash,
    # which the scraper mistook for a Cloudflare block.
    images = [
        {"src": "https://example.org/logo.svg", "alt": None, "desc": None, "score": 1},
        {"src": None, "alt": "photo", "desc": None, "score": 5},
    ]
    assert select_best_logo(images, validate=False) == "https://example.org/logo.svg"
