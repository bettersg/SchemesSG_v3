"""
URL health check utility.

Provides functions to check if URLs are accessible using HTTP HEAD requests.
Falls back to GET for servers that block HEAD requests.
"""
import requests
from typing import Dict, Any, Optional
from loguru import logger

# Use a browser-like User-Agent to avoid being blocked
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def check_link_health(
    url: str,
    timeout: int = 10,
    max_redirects: int = 3
) -> Dict[str, Any]:
    """
    Check if a URL is accessible using HTTP HEAD request.

    Uses HEAD request for efficiency (faster, less bandwidth than GET).
    Falls back to GET request for 403/405 errors (common with gov sites).
    Follows redirects up to max_redirects.

    Args:
        url: The URL to check
        timeout: Request timeout in seconds (default 10)
        max_redirects: Maximum number of redirects to follow (default 3)

    Returns:
        dict with:
            - alive: bool - True if URL is accessible
            - status_code: int - HTTP status code (0 if connection failed)
            - error: str|None - Error message if not alive
            - final_url: str|None - Final URL after redirects
    """
    if not url:
        return {
            "alive": False,
            "status_code": 0,
            "error": "Empty URL",
            "final_url": None
        }

    # Ensure URL has scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        # Use HEAD request (faster, less bandwidth)
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "User-Agent": BROWSER_USER_AGENT
            }
        )

        # Check redirect count
        if len(response.history) > max_redirects:
            return {
                "alive": False,
                "status_code": response.status_code,
                "error": f"Too many redirects ({len(response.history)})",
                "final_url": response.url
            }

        # 2xx = success
        if 200 <= response.status_code < 300:
            return {
                "alive": True,
                "status_code": response.status_code,
                "error": None,
                "final_url": response.url
            }

        # 3xx should have been followed, but check just in case
        if 300 <= response.status_code < 400:
            return {
                "alive": True,
                "status_code": response.status_code,
                "error": None,
                "final_url": response.url
            }

        # 4xx = client errors (dead link)
        if 400 <= response.status_code < 500:
            error_messages = {
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                405: "Method Not Allowed",
                410: "Gone",
                429: "Rate Limited",
            }
            error = error_messages.get(
                response.status_code,
                f"HTTP {response.status_code}"
            )

            # 429 is rate limiting - don't mark as dead
            if response.status_code == 429:
                return {
                    "alive": True,  # Don't mark as dead, just rate limited
                    "status_code": response.status_code,
                    "error": "Rate limited - skipped",
                    "final_url": response.url
                }

            # 405 Method Not Allowed - try GET as fallback
            if response.status_code == 405:
                return _check_with_get(url, timeout)

            # 403 Forbidden - often Cloudflare/bot protection, not truly dead
            # Don't mark as dead, treat as "uncertain" (alive but with warning)
            if response.status_code == 403:
                get_result = _check_with_get(url, timeout)
                if get_result["alive"]:
                    return get_result
                # Still 403 after GET - likely bot protection, not dead link
                return {
                    "alive": True,  # Don't mark as dead
                    "status_code": 403,
                    "error": "Blocked by bot protection (Cloudflare/WAF) - manual check needed",
                    "final_url": response.url
                }

            return {
                "alive": False,
                "status_code": response.status_code,
                "error": error,
                "final_url": response.url
            }

        # 5xx = server errors (might be temporary)
        if response.status_code >= 500:
            error_messages = {
                500: "Internal Server Error",
                502: "Bad Gateway",
                503: "Service Unavailable",
                504: "Gateway Timeout",
            }
            return {
                "alive": False,
                "status_code": response.status_code,
                "error": error_messages.get(
                    response.status_code,
                    f"Server Error {response.status_code}"
                ),
                "final_url": response.url
            }

        # Unknown status
        return {
            "alive": False,
            "status_code": response.status_code,
            "error": f"Unknown status {response.status_code}",
            "final_url": response.url
        }

    except requests.exceptions.Timeout:
        return {
            "alive": False,
            "status_code": 0,
            "error": f"Connection timeout ({timeout}s)",
            "final_url": None
        }

    except requests.exceptions.SSLError as e:
        return {
            "alive": False,
            "status_code": 0,
            "error": f"SSL Error: {str(e)[:100]}",
            "final_url": None
        }

    except requests.exceptions.ConnectionError as e:
        error_str = str(e)
        if "NameResolutionError" in error_str or "Name or service not known" in error_str:
            return {
                "alive": False,
                "status_code": 0,
                "error": "DNS resolution failed",
                "final_url": None
            }
        return {
            "alive": False,
            "status_code": 0,
            "error": f"Connection failed: {error_str[:100]}",
            "final_url": None
        }

    except requests.exceptions.TooManyRedirects:
        return {
            "alive": False,
            "status_code": 0,
            "error": "Too many redirects",
            "final_url": None
        }

    except Exception as e:
        logger.error(f"Unexpected error checking {url}: {e}")
        return {
            "alive": False,
            "status_code": 0,
            "error": f"Unexpected error: {str(e)[:100]}",
            "final_url": None
        }


def _check_with_get(url: str, timeout: int) -> Dict[str, Any]:
    """
    Fallback check using GET request.

    Some servers don't support HEAD requests (405).
    Use GET with stream=True to avoid downloading body.
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,  # Don't download body
            headers={
                "User-Agent": BROWSER_USER_AGENT
            }
        )
        response.close()  # Close without reading body

        if 200 <= response.status_code < 400:
            return {
                "alive": True,
                "status_code": response.status_code,
                "error": None,
                "final_url": response.url
            }

        return {
            "alive": False,
            "status_code": response.status_code,
            "error": f"HTTP {response.status_code}",
            "final_url": response.url
        }

    except Exception as e:
        return {
            "alive": False,
            "status_code": 0,
            "error": f"GET fallback failed: {str(e)[:100]}",
            "final_url": None
        }
