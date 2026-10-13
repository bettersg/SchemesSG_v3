
import asyncio
import gzip
import logging
import re
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit, unquote
from urllib.robotparser import RobotFileParser

import httpx
from defusedxml import ElementTree as ET
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

COMMON_SITEMAPS = (
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/wp-sitemap.xml",
    "/sitemap.xml.gz",
)

MAX_SITEMAPS = 30
MAX_DEPTH = 4
MAX_URLS = 50000
MAX_BYTES = 10 * 1024 * 1024

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".pdf", ".zip", ".css", ".js", ".svg",
)


@dataclass
class SitemapResult:
    sitemap_urls: list[str] = field(default_factory=list)
    page_urls: list[str] = field(default_factory=list)
    candidates: list[tuple[str, float]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    return parts._replace(fragment="").geturl()


def allowed_host(url: str, base_url: str) -> bool:
    """Allow the organisation host and its subdomains."""
    host = (urlsplit(url).hostname or "").lower()
    base = (urlsplit(base_url).hostname or "").lower()

    def strip_www(h):
        return h[4:] if h.startswith("www.") else h

    host, base = strip_www(host), strip_www(base)
    return host == base or host.endswith("." + base)


def score_url(
    url: str,
    scheme_name: str,
    previous_link: str,
) -> float:
    """Rank sitemap URLs without fetching page content."""
    path = unquote(urlsplit(url).path).lower()
    path_text = re.sub(r"[-_/]+", " ", path).strip()
    name = scheme_name.lower().strip()

    if not path_text:
        return 0.0

    similarity = fuzz.token_set_ratio(name, path_text)

    old_path = urlsplit(previous_link).path.lower()
    old_slug = old_path.rstrip("/").split("/")[-1]
    old_slug = unquote(old_slug).replace("-", " ")

    old_similarity = (
        fuzz.token_set_ratio(old_slug, path_text)
        if old_slug else 0
    )

    score = max(similarity, old_similarity * 0.9)

    # Prefer potentially relevant programme directories.
    if any(word in path for word in (
        "programme", "program", "scheme",
        "service", "support", "grant", "fund"
    )):
        score += 5

    return min(score, 100.0)


async def fetch(
    client: httpx.AsyncClient,
    url: str,
    base_url: str,
) -> tuple[str, bytes] | None:
    """Fetch a resource with basic redirect and size checks."""
    try:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            final_url = str(response.url)

            if not allowed_host(final_url, base_url):
                return None

            chunks = []
            size = 0

            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("Resource exceeds size limit")
                chunks.append(chunk)

            return final_url, b"".join(chunks)

    except (httpx.HTTPError, ValueError) as exc:
        logger.debug("Fetch failed for %s: %s", url, exc)
        return None


async def discover_sitemap_urls(
    client: httpx.AsyncClient,
    base_url: str,
) -> list[str]:
    """Discover sitemap URLs from robots.txt and common paths."""
    discovered = []

    robots_url = urljoin(base_url, "/robots.txt")
    result = await fetch(client, robots_url, base_url)

    if result:
        _, content = result

        parser = RobotFileParser()
        parser.parse(
            content.decode("utf-8-sig", errors="replace").splitlines()
        )

        discovered.extend(parser.site_maps() or [])

    discovered.extend(
        urljoin(base_url, path)
        for path in COMMON_SITEMAPS
    )

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(discovered))


def parse_sitemap(
    content: bytes,
    url: str,
) -> tuple[str, list[str]]:
    """Parse XML sitemap indexes and URL sets."""
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
        if len(content) > MAX_BYTES:
            raise ValueError("Decompressed sitemap too large")

    root = ET.fromstring(content)
    root_type = root.tag.split("}")[-1].lower()

    if root_type not in ("sitemapindex", "urlset"):
        raise ValueError(f"Unsupported XML root: {root_type}")

    urls = []

    for child in root:
        if child.tag.split("}")[-1].lower() not in ("sitemap", "url"):
            continue

        for element in child:
            if element.tag.split("}")[-1].lower() == "loc":
                if element.text:
                    urls.append(element.text.strip())
                break

    return root_type, urls


async def discover_relevant_pages(
    scheme_name: str,
    previous_link: str,
    top_k: int = 10,
) -> SitemapResult:
    """Discover and rank sitemap URLs for Browser Use."""
    result = SitemapResult()

    parts = urlsplit(previous_link)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        result.errors.append("Invalid previous URL")
        return result

    base_url = f"{parts.scheme}://{parts.netloc}/"

    timeout = httpx.Timeout(10.0, connect=5.0)

    async with httpx.AsyncClient(
        follow_redirects=True,
        max_redirects=5,
        timeout=timeout,
        headers={"User-Agent": "SchemesSG-LinkChecker/1.0"},
    ) as client:

        seeds = await discover_sitemap_urls(client, base_url)
        queue = deque((url, 0) for url in seeds)
        visited = set()
        pages = set()

        while queue and len(visited) < MAX_SITEMAPS:
            sitemap_url, depth = queue.popleft()
            sitemap_url = normalize_url(sitemap_url)

            if sitemap_url in visited or depth > MAX_DEPTH:
                continue

            visited.add(sitemap_url)

            if not allowed_host(sitemap_url, base_url):
                continue

            fetched = await fetch(client, sitemap_url, base_url)
            if not fetched:
                continue

            final_url, content = fetched

            try:
                kind, urls = parse_sitemap(content, final_url)
            except Exception as exc:
                result.errors.append(
                    f"{final_url}: {type(exc).__name__}"
                )
                continue

            result.sitemap_urls.append(final_url)

            if kind == "sitemapindex":
                for child_url in urls:
                    child_url = urljoin(final_url, child_url)
                    if allowed_host(child_url, base_url):
                        queue.append((child_url, depth + 1))

            elif kind == "urlset":
                for page_url in urls:
                    page_url = normalize_url(
                        urljoin(final_url, page_url)
                    )

                    if not allowed_host(page_url, base_url):
                        continue

                    if urlsplit(page_url).path.lower().endswith(
                        SKIP_EXTENSIONS
                    ):
                        continue

                    pages.add(page_url)

                    if len(pages) >= MAX_URLS:
                        break

            if len(pages) >= MAX_URLS:
                break

        result.page_urls = sorted(pages)

        ranked = [
            (
                url,
                score_url(url, scheme_name, previous_link)
            )
            for url in pages
        ]

        ranked.sort(key=lambda item: item[1], reverse=True)
        result.candidates = ranked[:top_k]

    return result
