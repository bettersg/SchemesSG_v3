"""
Web scraping with crawl4ai + Playwright.

Handles web content extraction with Cloudflare bypass support via Pydoll.
"""
import io
import os
import re
import asyncio
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from loguru import logger

from app.constants import CLOUDFLARE_INDICATORS, BOT_PROTECTION_INDICATORS
from app.services.extraction import select_best_logo


async def scrape_url(url: str) -> Dict[str, Any]:
    """
    Scrape a URL and return content with images.

    Handles PDF files separately. Uses crawl4ai for HTML pages.

    Args:
        url: URL to scrape

    Returns:
        Dict with: content, images, logo_url, error
    """
    if _is_pdf(url):
        return await _scrape_pdf(url)
    return await _scrape_html(url)


def _is_pdf(url: str) -> bool:
    """Check if URL points to a PDF file."""
    return url.lower().endswith('.pdf')


async def _scrape_pdf(url: str) -> Dict[str, Any]:
    """Extract text from PDF URL."""
    logger.info(f"PDF detected, using PDF extraction: {url}")

    try:
        from pypdf import PdfReader

        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()

        pdf_file = io.BytesIO(response.content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            return {
                "content": "",
                "images": [],
                "logo_url": None,
                "error": "PDF Processing Error: No text extracted"
            }

        return {
            "content": text.strip(),
            "images": [],
            "logo_url": None,
            "error": None
        }

    except Exception as e:
        return {
            "content": "",
            "images": [],
            "logo_url": None,
            "error": f"PDF Processing Error: {str(e)}"
        }


async def _scrape_html(url: str) -> Dict[str, Any]:
    """Scrape HTML with crawl4ai, fallback to Pydoll for Cloudflare."""
    result = await _try_crawl4ai(url)

    # Check if blocked by Cloudflare - try Pydoll bypass
    if _is_cloudflare_blocked(result):
        logger.warning(f"Cloudflare detected, trying Pydoll bypass for: {url}")
        pydoll_result = await _try_pydoll_bypass(url)
        if pydoll_result.get("content") and not pydoll_result.get("error"):
            return pydoll_result
        # Pydoll failed too
        result["error"] = f"MANUAL_REVIEW_NEEDED: Cloudflare protected - {pydoll_result.get('error', 'Pydoll failed')}"

    return result


def _is_cloudflare_blocked(result: Dict[str, Any]) -> bool:
    """Check if content indicates Cloudflare blocking."""
    if result.get("error"):
        error_lower = result["error"].lower()
        if any(ind in error_lower for ind in BOT_PROTECTION_INDICATORS):
            return True

    content = result.get("content", "")
    content_lower = content.lower() if content else ""

    # Short content or Cloudflare indicators
    if len(content) < 500:
        return True

    return any(ind in content_lower for ind in CLOUDFLARE_INDICATORS)


async def _try_crawl4ai(url: str) -> Dict[str, Any]:
    """Try scraping with crawl4ai."""
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        browser_config = BrowserConfig(
            headless=True,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--disable-extensions",
            ]
        )

        crawl_config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(
                max_depth=1,
                include_external=False,
                max_pages=5
            ),
            cache_mode=CacheMode.BYPASS,
            verbose=False
        )

        logger.info(f"Starting crawl4ai for: {url}")

        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(url=url, config=crawl_config, magic=True)

        return _process_crawl_results(results, url)

    except Exception as e:
        error_str = str(e).lower()
        if any(ind in error_str for ind in BOT_PROTECTION_INDICATORS):
            return {
                "content": "",
                "images": [],
                "logo_url": None,
                "error": f"Bot protection detected: {str(e)}"
            }
        logger.error(f"Crawl4ai error for {url}: {e}")
        return {
            "content": "",
            "images": [],
            "logo_url": None,
            "error": f"Crawl Error: {str(e)}"
        }


def _process_crawl_results(results, url: str) -> Dict[str, Any]:
    """Process crawl4ai results into standardized format."""
    if not results:
        return {
            "content": "",
            "images": [],
            "logo_url": None,
            "error": "No results from crawler"
        }

    # Handle list results (deep crawl)
    if isinstance(results, list):
        all_text = []
        all_images = []

        for result in results:
            if result.success:
                text = result.markdown or result.cleaned_html or ""
                if text:
                    all_text.append(text)

                if hasattr(result, 'media') and result.media:
                    images = result.media.get('images', [])
                    all_images.extend(images)

        scraped_text = "\n\n---PAGE BREAK---\n\n".join(all_text)
        logo_url = select_best_logo(all_images, url) if all_images else None

        return {
            "content": scraped_text,
            "images": all_images,
            "logo_url": logo_url,
            "error": None
        }

    # Single result
    if not results.success:
        error_msg = results.error_message or "Unknown crawl error"
        return {
            "content": "",
            "images": [],
            "logo_url": None,
            "error": error_msg
        }

    scraped_text = results.markdown or results.cleaned_html or ""
    images = []
    logo_url = None

    if hasattr(results, 'media') and results.media:
        images = results.media.get('images', [])
        if images:
            logo_url = select_best_logo(images, url)

    logger.info(f"Crawl4ai completed for {url}: {len(scraped_text)} chars")
    return {
        "content": scraped_text,
        "images": images,
        "logo_url": logo_url,
        "error": None
    }


async def _try_pydoll_bypass(url: str) -> Dict[str, Any]:
    """
    Try Pydoll for Cloudflare bypass.

    Uses Xvfb virtual display for better Cloudflare bypass.
    """
    xvfb_process = None

    try:
        from pydoll.browser import Chrome
        from pydoll.browser.options import ChromiumOptions

        logger.info(f"Starting Pydoll Cloudflare bypass for: {url}")

        # Start Xvfb virtual display
        display_num = 99
        os.environ["DISPLAY"] = f":{display_num}"

        try:
            xvfb_process = subprocess.Popen(
                ["Xvfb", f":{display_num}", "-screen", "0", "1920x1080x24"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await asyncio.sleep(1)
            logger.info(f"Started Xvfb on :{display_num}")
        except FileNotFoundError:
            logger.warning("Xvfb not found, using headless mode")
            xvfb_process = None
        except Exception as e:
            logger.warning(f"Failed to start Xvfb: {e}")
            xvfb_process = None

        # Configure browser
        options = ChromiumOptions()
        chromium_paths = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            os.environ.get("CHROME_PATH", ""),
        ]
        for path in chromium_paths:
            if path and os.path.exists(path):
                options.binary_location = path
                logger.info(f"Using Chromium at: {path}")
                break

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        if xvfb_process is None:
            options.add_argument("--headless=new")

        logger.info("Starting Pydoll browser...")
        async with Chrome(options=options) as browser:
            tab = await browser.start()
            logger.info("Pydoll browser started")

            try:
                await tab.enable_auto_solve_cloudflare_captcha()
                logger.info("Cloudflare auto-solve enabled")
            except Exception as cf_err:
                logger.warning(f"Could not enable cloudflare bypass: {cf_err}")

            await tab.go_to(url)
            logger.info(f"Navigated to {url}")

            # Wait for Cloudflare challenge
            await asyncio.sleep(15)

            # Check if still on challenge page
            for attempt in range(3):
                try:
                    title = await tab.execute_script("return document.title")
                    logger.info(f"Page title (attempt {attempt + 1}): {title}")
                    if title and any(
                        ind in str(title).lower()
                        for ind in ["just a moment", "attention required", "checking"]
                    ):
                        logger.info("Still on Cloudflare challenge, waiting...")
                        await asyncio.sleep(10)
                    else:
                        break
                except Exception:
                    break

            # Extract page content
            page_content = await _extract_pydoll_content(tab)

            if page_content and len(page_content) > 500:
                logger.info(f"Pydoll succeeded for {url}: {len(page_content)} chars")
                images = _extract_images_from_html(page_content, url)
                logo_url = select_best_logo(images, url) if images else None
                return {
                    "content": page_content,
                    "images": images,
                    "logo_url": logo_url,
                    "error": None
                }
            else:
                return {
                    "content": "",
                    "images": [],
                    "logo_url": None,
                    "error": "Pydoll: Content too short (Cloudflare may still be blocking)"
                }

    except ImportError as e:
        logger.warning(f"Pydoll not installed: {e}")
        return {"content": "", "images": [], "logo_url": None, "error": "Pydoll not installed"}
    except Exception as e:
        logger.error(f"Pydoll error for {url}: {e}")
        return {"content": "", "images": [], "logo_url": None, "error": f"Pydoll error: {str(e)}"}
    finally:
        if xvfb_process:
            try:
                xvfb_process.terminate()
                xvfb_process.wait(timeout=5)
            except Exception:
                try:
                    xvfb_process.kill()
                except Exception:
                    pass


async def _extract_pydoll_content(tab) -> str:
    """Extract page content from Pydoll tab."""

    def extract_cdp_value(result):
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            try:
                if 'result' in result:
                    inner = result['result']
                    if isinstance(inner, dict) and 'result' in inner:
                        inner = inner['result']
                    if isinstance(inner, dict) and 'value' in inner:
                        return str(inner['value'])
                if 'value' in result:
                    return str(result['value'])
            except Exception:
                pass
        return str(result)

    page_content = ""

    # Method 1: outerHTML
    try:
        result = await tab.execute_script("return document.documentElement.outerHTML")
        extracted = extract_cdp_value(result)
        if extracted and len(extracted) > 10:
            page_content = extracted
            logger.info(f"Pydoll outerHTML: {len(page_content)} chars")
    except Exception as e:
        logger.warning(f"Pydoll outerHTML failed: {e}")

    # Method 2: innerHTML
    if len(page_content) < 100:
        try:
            result = await tab.execute_script("return document.body.innerHTML")
            extracted = extract_cdp_value(result)
            if extracted and len(extracted) > len(page_content):
                page_content = extracted
                logger.info(f"Pydoll innerHTML: {len(page_content)} chars")
        except Exception as e:
            logger.warning(f"Pydoll innerHTML failed: {e}")

    return page_content


def _extract_images_from_html(html: str, base_url: str) -> List[Dict]:
    """Extract images from HTML for logo detection."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, 'lxml')
    images = []

    for img in soup.find_all('img'):
        src = img.get('src', '')
        if not src or src.startswith('data:'):
            continue

        # Build description from parent context
        desc_parts = []
        for parent in img.parents:
            if parent.name in ['header', 'nav', 'footer', 'aside']:
                desc_parts.append(parent.name)
            parent_class = parent.get('class', [])
            if parent_class:
                desc_parts.extend(parent_class if isinstance(parent_class, list) else [parent_class])
            if len(desc_parts) > 5:
                break

        images.append({
            'src': src,
            'alt': img.get('alt', ''),
            'desc': ' '.join(desc_parts),
            'score': 0
        })

    return images
