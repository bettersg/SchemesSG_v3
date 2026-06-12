"""Fetch-a-webpage tool for agent use.

Web *search* only returns snippets. To actually find a contact, phone, email, or
application step that lives in a page body or a child page (e.g. /contact), the
agent needs to read the real page. This tool fetches a URL and returns its clean
main-content text (via Trafilatura, which strips nav/footer/boilerplate) plus the
page's navigable links, so the agent can follow a likely child link. The router
prompt caps how many fetches it does per turn.
"""

import asyncio
import os
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse

import trafilatura
from trafilatura.settings import use_config
from lxml import html as lxml_html
from langgraph.config import get_stream_writer
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from utils.check_link import BROWSER_USER_AGENT
from utils.logging_setup import setup_logging


logger = setup_logging(level=os.getenv("AGENT_DEBUG_LOG_LEVEL", "DEBUG"))

# Trafilatura's default user-agent (its own crawler string) is blocked by many
# government and institutional sites (e.g. aic.sg, moh.gov.sg), which causes the
# download to silently return nothing. Present a normal browser UA instead.
_TRAFILATURA_CONFIG = use_config()
_TRAFILATURA_CONFIG.set("DEFAULT", "user_agents", BROWSER_USER_AGENT)
_TRAFILATURA_CONFIG.set("DEFAULT", "sleep_time", "0")

ACTION_MESSAGE_ON_START = 'Reading the page "{url}"'
ACTION_MESSAGE_ON_END = 'Read "{url}".'
ACTION_MESSAGE_ON_FAIL = 'Couldn\'t read "{url}".'
SHORT_ACTION_MESSAGE_ON_START = "Reading a web page"
SHORT_ACTION_MESSAGE_ON_END = "Web page read"
SHORT_ACTION_MESSAGE_ON_FAIL = "Web page unavailable"


def _emit_action_message(label: str, message: str) -> None:
    """Best-effort stream event for the live status trace. Never raises."""
    try:
        writer = get_stream_writer()
        writer(
            {
                "type": "action_message",
                "data": {
                    "phase": "action_message",
                    "label": label,
                    "message": message,
                },
            }
        )
    except Exception as e:
        logger.debug(f"Failed to emit action message to stream: {e}")

# Keep returned text bounded so a long page doesn't blow up the agent's context.
MAX_TEXT_CHARS = 6000
MAX_LINKS = 40
REQUEST_TIMEOUT_SECONDS = 8.0


def extract_links(html: str, base_url: str) -> list[dict[str, str]]:
    """Return a deduped list of labelled, absolute links from the page.

    Same-domain links come first (the answer is usually on the same site) and
    each carries its anchor text so the agent can pick a sensible child page
    (e.g. one labelled "Contact" or "About"). Pure function for easy testing.
    """
    try:
        doc = lxml_html.fromstring(html)
    except Exception:
        return []

    base_domain = urlparse(base_url).netloc
    # Strip the fragment from the base so same-page anchors (e.g. "#top") can be
    # recognised and dropped after absolutization.
    base_no_fragment = urljoin(base_url, urlparse(base_url)._replace(fragment="").geturl())
    seen: set[str] = set()
    same_domain: list[dict[str, str]] = []
    other_domain: list[dict[str, str]] = []

    for anchor in doc.xpath("//a[@href]"):
        raw_href = (anchor.get("href") or "").strip()
        # Drop non-navigational schemes and pure same-page fragments up front.
        if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        absolute = urljoin(base_url, raw_href)
        if not absolute.startswith(("http://", "https://")):
            continue
        # Normalise away the fragment; a link that points back at this same page
        # carries no new content for the agent to follow.
        normalized = urljoin(absolute, urlparse(absolute)._replace(fragment="").geturl())
        if normalized == base_no_fragment or normalized in seen:
            continue
        seen.add(normalized)

        label = " ".join(anchor.text_content().split())[:80]
        entry = {"label": label, "url": normalized}
        if urlparse(normalized).netloc == base_domain:
            same_domain.append(entry)
        else:
            other_domain.append(entry)

    return (same_domain + other_domain)[:MAX_LINKS]


def _download_html(url: str) -> str | None:
    """Download a page's HTML, with a plain-urllib fallback.

    Trafilatura's downloader fails on some sites (e.g. aic.sg) that a normal
    browser-UA request fetches fine, so fall back to urllib before giving up.
    """
    raw = trafilatura.fetch_url(url, config=_TRAFILATURA_CONFIG)
    if raw:
        return raw
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except Exception as e:
        logger.debug(f"urllib fallback download failed | url={url} | {e}")
        return None


def _fetch_webpage_sync(url: str) -> dict[str, Any]:
    logger.info(f"fetch_webpage tool invoked | url={url}")
    _emit_action_message(
        SHORT_ACTION_MESSAGE_ON_START, ACTION_MESSAGE_ON_START.format(url=url)
    )

    try:
        raw = _download_html(url)
        if not raw:
            # Emit a closing status so the live trace doesn't strand on
            # "Reading the page …" forever when a site blocks or times us out.
            _emit_action_message(
                SHORT_ACTION_MESSAGE_ON_FAIL, ACTION_MESSAGE_ON_FAIL.format(url=url)
            )
            return {"url": url, "error": "fetch_webpage failed: could not download page"}

        # Clean main-content text (boilerplate stripped), plus navigable links.
        text = trafilatura.extract(raw, output_format="markdown", url=url) or ""
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS] + " …[truncated]"
        links = extract_links(raw, url)

        _emit_action_message(
            SHORT_ACTION_MESSAGE_ON_END, ACTION_MESSAGE_ON_END.format(url=url)
        )
        return {"url": url, "text": text, "links": links}
    except Exception as e:
        logger.exception("fetch_webpage failed")
        _emit_action_message(
            SHORT_ACTION_MESSAGE_ON_FAIL, ACTION_MESSAGE_ON_FAIL.format(url=url)
        )
        return {"url": url, "error": f"fetch_webpage failed: {e}"}


async def _fetch_webpage_async(url: str) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_fetch_webpage_sync, url),
            timeout=REQUEST_TIMEOUT_SECONDS + 2.0,
        )
    except asyncio.TimeoutError:
        logger.warning("fetch_webpage timed out")
        _emit_action_message(
            SHORT_ACTION_MESSAGE_ON_FAIL, ACTION_MESSAGE_ON_FAIL.format(url=url)
        )
        return {"url": url, "error": "fetch_webpage timed out"}


class FetchWebpageInput(BaseModel):
    url: str = Field(
        ...,
        description=(
            "The full URL of a webpage to read. Use this to read an actual page's "
            "content (e.g. a scheme's official site or a /contact page) when a web "
            "search only gave snippets. The result includes the page's clean text "
            "and its links, so you can follow a relevant link (such as a contact or "
            "about page) and fetch that next."
        ),
    )


fetch_webpage_tool = StructuredTool.from_function(
    func=_fetch_webpage_sync,
    coroutine=_fetch_webpage_async,
    name="fetch_webpage",
    description=(
        "Read the clean main-content text and links of a specific webpage. Use after "
        "a web search when you need details a snippet doesn't contain (contact info, "
        "application steps), and follow the returned links into child pages when needed."
    ),
    args_schema=FetchWebpageInput,
)
