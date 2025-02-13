from typing import Dict, Union

from firebase_functions import https_fn


# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development
    "https://schemessg-v3-dev.web.app",  # dev frontend
    "https://schemessg-v3-dev.firebaseapp.com",  # dev frontend
    "https://schemessg-v3-dev.firebaseapp.com",  # dev frontend
    "https://staging.schemes.sg",  # Production frontend
    "https://schemes.firebaseapp.com",  # Production frontend
    "https://schemes.sg",  # Production frontend
]


def get_cors_headers(request: https_fn.Request) -> Dict[str, str]:
    """
    Return CORS headers based on the request origin.
    Only allows specific origins.

    Args:
        request: The incoming request containing origin information
    """
    origin = request.headers.get("Origin", "")

    # Only allow specified origins
    if origin in ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }

    # If origin not allowed, return headers without Access-Control-Allow-Origin
    return {
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }


def handle_cors_preflight(
    request: https_fn.Request, allowed_methods: str = "GET, POST, OPTIONS"
) -> Union[https_fn.Response, tuple]:
    """
    Handle CORS preflight requests with origin validation

    Args:
        request: The incoming request
        allowed_methods: Allowed HTTP methods
    """
    headers = get_cors_headers(request)
    headers["Access-Control-Allow-Methods"] = allowed_methods

    # If origin wasn't in allowed list, get_cors_headers won't include Allow-Origin
    # In that case, return 403 Forbidden
    if "Access-Control-Allow-Origin" not in headers:
        return https_fn.Response(response="Origin not allowed", status=403, headers=headers)

    return https_fn.Response(response="", status=204, headers=headers)
