"""
URL utilities for duplicate scheme detection.

Provides domain extraction and duplicate checking functionality.
"""
from urllib.parse import urlparse
from typing import Optional, Dict, Any

from firebase_admin import firestore
from loguru import logger


def extract_domain(url: str) -> str:
    """
    Extract domain from URL for duplicate comparison.

    Examples:
        https://www.probono.sg/get-legal-help/ -> probono.sg
        https://probono.sg -> probono.sg
        http://WWW.Example.COM/path -> example.com

    Args:
        url: The URL to extract domain from

    Returns:
        Lowercase domain without www prefix, or empty string if invalid
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

    return hostname


def check_duplicate_scheme(url: str) -> Optional[Dict[str, Any]]:
    """
    Check if a scheme with the same domain already exists.

    Args:
        url: The URL to check (domain will be extracted)

    Returns:
        Dict with existing scheme info if duplicate found, None otherwise
    """
    submitted_domain = extract_domain(url)
    if not submitted_domain:
        return None

    logger.info(f"Checking for duplicate domain: {submitted_domain}")

    db = firestore.client()
    schemes_ref = db.collection("schemes")

    # Query all schemes and check domains
    docs = schemes_ref.stream()

    for doc in docs:
        data = doc.to_dict()
        existing_link = data.get("link", "")
        existing_domain = extract_domain(existing_link)

        if existing_domain == submitted_domain:
            logger.info(f"Found duplicate: {existing_link} (domain: {existing_domain})")
            # Try different field names for scheme name
            scheme_name = (
                data.get("scheme") or
                data.get("Scheme") or
                data.get("scheme_name") or
                data.get("name") or
                existing_domain  # Fallback to domain if no name found
            )
            return {
                "doc_id": doc.id,
                "scheme": scheme_name,
                "link": existing_link,
                "domain": existing_domain,
            }

    return None
