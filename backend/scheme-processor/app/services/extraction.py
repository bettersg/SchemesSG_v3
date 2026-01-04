"""
Domain Services for Scheme Data Extraction.

Contains business logic for contact extraction, category normalization, and logo selection.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from app.constants import HEADER_PATTERNS, LOGO_PATTERNS, NEGATIVE_PATTERNS
from loguru import logger


@dataclass
class ContactInfo:
    """Result from contact extraction (regex-based)."""

    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)


def extract_contacts(text: str, max_text_length: int = 100000) -> ContactInfo:
    """
    Extract contact information using regex patterns.

    More reliable than LLM for structured data like emails and phone numbers.

    Args:
        text: Raw text content to extract contacts from
        max_text_length: Maximum text length to process (prevents ReDoS)

    Returns:
        ContactInfo with extracted emails, phones, and addresses
    """
    if not text:
        return ContactInfo()

    # Truncate text to prevent ReDoS attacks with crafted input
    if len(text) > max_text_length:
        logger.warning(f"Text truncated from {len(text)} to {max_text_length} chars for contact extraction")
        text = text[:max_text_length]

    # Email regex - optimized to prevent catastrophic backtracking
    # Uses {1,64} limits instead of unbounded + quantifiers
    email_pattern = r"[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9.-]{1,253}\.[a-zA-Z]{2,10}"
    emails = re.findall(email_pattern, text)
    # Filter out common false positives (image/asset file extensions)
    invalid_extensions = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".ico")
    filtered_emails = [e for e in emails if not e.lower().endswith(invalid_extensions)]

    # Singapore phone patterns
    phone_patterns = [
        r"\+65[\s\-]?\d{4}[\s\-]?\d{4}",  # +65 format
        r"\(65\)[\s\-]?\d{4}[\s\-]?\d{4}",  # (65) format
        r"(?<!\d)[689]\d{3}[\s\-]?\d{4}(?!\d)",  # Local 8-digit (6/8/9 prefix)
        r"1800[\s\-]?\d{3}[\s\-]?\d{4}",  # Toll-free 1800
        r"1900[\s\-]?\d{3}[\s\-]?\d{4}",  # Premium 1900
    ]
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    # Clean and dedupe
    cleaned_phones = [re.sub(r"[\s\-]", "", p) for p in phones]

    # Singapore postal code pattern (6 digits)
    postal_pattern = r"Singapore\s*\d{6}|S\s*\(\s*\d{6}\s*\)|S\d{6}"
    postal_matches = re.findall(postal_pattern, text, re.IGNORECASE)

    return ContactInfo(
        emails=list(dict.fromkeys(filtered_emails)),  # Dedupe, preserve order
        phones=list(dict.fromkeys(cleaned_phones)),
        addresses=list(dict.fromkeys(postal_matches)),
    )


def normalize_categories(llm_values: Optional[List[str]], allowed_options: List[str]) -> List[str]:
    """
    Map LLM output values to valid category options using keyword matching.

    The LLM may return slightly different phrasings - this normalizes them
    to the canonical values in our category lists.

    Args:
        llm_values: Raw values from LLM extraction
        allowed_options: List of valid category values

    Returns:
        List of matched valid category values
    """
    if not llm_values:
        return []

    stop_words = {"and", "or", "the", "a", "an", "for", "of", "in", "to", "with"}

    def get_keywords(text: str) -> set:
        """Extract meaningful keywords from text."""
        words = text.lower().replace("/", " ").replace("-", " ").split()
        return {w for w in words if w not in stop_words and len(w) > 2}

    mapped = []
    for llm_val in llm_values:
        llm_lower = llm_val.lower().strip()
        llm_keywords = get_keywords(llm_val)

        # Try exact match first
        matched = False
        for opt in allowed_options:
            if llm_lower == opt.lower():
                mapped.append(opt)
                matched = True
                break

        # Try keyword overlap if no exact match
        if not matched:
            for opt in allowed_options:
                opt_keywords = get_keywords(opt)
                if llm_keywords & opt_keywords:  # Intersection
                    mapped.append(opt)
                    break

    return list(dict.fromkeys(mapped))  # Remove duplicates, preserve order


def validate_image_url(url: str, timeout: int = 5) -> bool:
    """
    Validate that an image URL is accessible and returns valid image content.

    Args:
        url: Image URL to validate
        timeout: Request timeout in seconds

    Returns:
        True if URL is accessible and returns image content-type
    """
    if not url or not url.startswith(("http://", "https://")):
        return False

    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            logger.debug(f"Image URL returned {response.status_code}: {url}")
            return False

        content_type = response.headers.get("content-type", "").lower()
        if "image" in content_type or url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")):
            return True

        logger.debug(f"Image URL has non-image content-type '{content_type}': {url}")
        return False

    except requests.exceptions.RequestException as e:
        logger.debug(f"Image URL validation failed: {url} - {e}")
        return False


def select_best_logo(images: List[Dict], base_url: str = "", validate: bool = True) -> Optional[str]:
    """
    Select the best logo image from a list of image candidates.

    Uses heuristics based on URL patterns, alt text, and context to identify
    the most likely logo image.

    Args:
        images: List of image dicts with 'src', 'alt', 'desc', 'score' keys
        base_url: Base URL for resolving relative image paths
        validate: Whether to validate URLs are accessible (default True)

    Returns:
        URL of the best logo candidate, or None if no suitable logo found
    """
    if not images:
        return None

    # Score all candidates
    scored_candidates = []

    for img in images:
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue

        src_lower = src.lower()
        alt_lower = img.get("alt", "").lower()
        desc_lower = img.get("desc", "").lower()
        score = img.get("score", 0) or 0

        # Strong boost for logo patterns in URL or alt
        if any(p in src_lower or p in alt_lower for p in LOGO_PATTERNS):
            score += 20

        # Boost for header/footer/nav location
        if any(p in src_lower or p in alt_lower or p in desc_lower for p in HEADER_PATTERNS):
            score += 15

        # Boost for SVG (common logo format)
        if ".svg" in src_lower:
            score += 10

        # Small boost for PNG with transparency (common for logos)
        if ".png" in src_lower:
            score += 3

        # Penalty for non-logo patterns
        if any(p in src_lower or p in alt_lower for p in NEGATIVE_PATTERNS):
            score -= 25

        if score > 0:
            # Convert relative URL to absolute
            absolute_url = src
            if base_url and not src.startswith(("http://", "https://")):
                absolute_url = urljoin(base_url, src)
            scored_candidates.append((score, absolute_url))

    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Return best valid URL
    for score, url in scored_candidates:
        if not validate or validate_image_url(url):
            logger.info(f"Selected logo URL (score={score}): {url}")
            return url
        else:
            logger.debug(f"Skipping invalid logo URL (score={score}): {url}")

    return None
