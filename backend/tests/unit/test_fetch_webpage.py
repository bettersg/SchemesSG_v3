"""Unit tests for fetch_webpage link extraction.

Behaviour under test: the fetched page yields a usable list of labelled links
(same-domain first, junk schemes dropped, relative URLs resolved, deduped) so
the agent can follow a child page. Text extraction is delegated to Trafilatura
(its own benchmarks cover that); network I/O is not tested here.
"""

from urllib.parse import urlparse

from agent.tools.fetch_webpage import extract_links


BASE = "https://example.org/programmes/aid.html"

HTML = """
<html><body>
  <h1>Family Aid</h1>
  <p>Monthly food and cash support for families.</p>
  <a href="/contact-us">Contact Us</a>
  <a href="about.html">About</a>
  <a href="#top">Skip</a>
  <a href="mailto:help@example.org">Email</a>
  <a href="tel:+6561234567">Call</a>
  <a href="https://other.org/partner">Partner site</a>
  <a href="/contact-us">Contact Us duplicate</a>
</body></html>
"""


def test_resolves_relative_links_to_absolute():
    urls = [link["url"] for link in extract_links(HTML, BASE)]
    assert "https://example.org/contact-us" in urls
    assert "https://example.org/programmes/about.html" in urls


def test_drops_anchor_mailto_tel_and_dedupes():
    urls = [link["url"] for link in extract_links(HTML, BASE)]
    assert not any(u.startswith(("mailto:", "tel:")) for u in urls)
    assert all("#top" not in u for u in urls)
    assert urls.count("https://example.org/contact-us") == 1  # deduped


def test_same_domain_links_come_first():
    links = extract_links(HTML, BASE)
    # Compare exact hosts (not URL string prefixes) so the ordering check can't
    # be fooled by a host like "example.org.evil.com".
    other = next(i for i, l in enumerate(links) if urlparse(l["url"]).netloc == "other.org")
    same = [i for i, l in enumerate(links) if urlparse(l["url"]).netloc == "example.org"]
    assert all(i < other for i in same)


def test_links_carry_anchor_label():
    contact = next(l for l in extract_links(HTML, BASE) if l["url"] == "https://example.org/contact-us")
    assert "Contact" in contact["label"]


def test_malformed_html_returns_empty_not_crash():
    assert extract_links("", BASE) == []
