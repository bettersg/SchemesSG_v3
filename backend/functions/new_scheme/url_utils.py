"""
URL utilities for duplicate scheme detection.

Provides URL normalization and duplicate checking functionality.
"""
from urllib.parse import urlparse, urlunparse
from typing import Optional, Dict, Any

from firebase_admin import firestore
from loguru import logger


def normalize_url(url: str) -> str:
    """
    Normalize URL for duplicate comparison.

    Normalizes by:
    - Converting to lowercase
    - Removing www. prefix
    - Removing trailing slashes
    - Removing query parameters and fragments
    - Keeping domain + path

    Examples:
        https://www.mtfa.org/darul-ihsan-orphanage/ -> mtfa.org/darul-ihsan-orphanage
        https://MTFA.org/ikcfundraising?ref=123 -> mtfa.org/ikcfundraising
        http://www.example.com -> example.com

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string (domain + path), or empty string if invalid
    """
    if not url:
        return ""

    url = url.strip().lower()

    # Add scheme if missing (urlparse needs it)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = parsed.netloc

    # Remove www. prefix
    if hostname.startswith("www."):
        hostname = hostname[4:]

    # Remove port if present
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    # Get path and remove trailing slashes
    path = parsed.path.rstrip("/")

    # Combine domain + path
    normalized = hostname + path

    return normalized


def extract_domain(url: str) -> str:
    """
    Extract domain from URL (for display purposes).

    Args:
        url: The URL to extract domain from

    Returns:
        Lowercase domain without www prefix
    """
    if not url:
        return ""

    url = url.strip().lower()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = parsed.netloc

    if hostname.startswith("www."):
        hostname = hostname[4:]

    if ":" in hostname:
        hostname = hostname.split(":")[0]

    return hostname


def check_duplicate_scheme(url: str) -> Optional[Dict[str, Any]]:
    """
    Check if a scheme with the same URL already exists.

    Compares normalized URLs (domain + path) to allow multiple schemes
    from the same domain but different pages.

    Examples:
        mtfa.org/darul-ihsan-orphanage != mtfa.org/ikcfundraising (different schemes)
        mtfa.org/orphanage == www.mtfa.org/orphanage/ (same scheme)

    Args:
        url: The URL to check

    Returns:
        Dict with existing scheme info if duplicate found, None otherwise
    """
    submitted_normalized = normalize_url(url)
    if not submitted_normalized:
        return None

    logger.info(f"Checking for duplicate URL: {submitted_normalized}")

    db = firestore.client()
    schemes_ref = db.collection("schemes")

    # Query all schemes and check normalized URLs
    docs = schemes_ref.stream()

    for doc in docs:
        data = doc.to_dict()
        existing_link = data.get("link", "")
        existing_normalized = normalize_url(existing_link)

        if existing_normalized == submitted_normalized:
            logger.info(f"Found duplicate: {existing_link} (normalized: {existing_normalized})")
            # Try different field names for scheme name
            scheme_name = (
                data.get("scheme") or
                data.get("Scheme") or
                data.get("scheme_name") or
                data.get("name") or
                extract_domain(existing_link)  # Fallback to domain if no name found
            )
            return {
                "doc_id": doc.id,
                "scheme": scheme_name,
                "link": existing_link,
                "normalized_url": existing_normalized,
            }

    return None
