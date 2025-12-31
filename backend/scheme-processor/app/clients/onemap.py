"""
OneMap API Integration for Planning Area extraction.

Extracts Singapore planning area from addresses using OneMap geocoding API.
"""
import os
import re
from typing import Optional

import requests
from loguru import logger


class PlanningAreaService:
    """
    Extract planning area from Singapore addresses using OneMap API.

    Uses geocoding to get coordinates, then queries planning area API.
    """

    def __init__(self):
        """Initialize service and obtain API token."""
        self._token = self._get_onemap_token()

    def _get_onemap_token(self) -> Optional[str]:
        """Get OneMap API access token using credentials from environment."""
        email = os.getenv("ONEMAP_EMAIL")
        password = os.getenv("ONEMAP_EMAIL_PASSWORD")

        if not email or not password:
            logger.warning("OneMap credentials not configured")
            return None

        try:
            response = requests.post(
                "https://www.onemap.gov.sg/api/auth/post/getToken",
                json={"email": email, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.warning(f"OneMap auth failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get OneMap token: {e}")

        return None

    def get_planning_area(self, address: str) -> Optional[str]:
        """
        Extract planning area from Singapore address.

        Args:
            address: Full address string (may contain postal code)

        Returns:
            Planning area name (e.g., "TAMPINES", "BEDOK") or None if not found
        """
        if not address or not self._token:
            return None

        # Handle comma-separated addresses (use first one)
        if "," in address:
            address = address.split(",")[0].strip()

        try:
            # Extract postal code if present (6 digits)
            postal_match = re.search(r'\b(\d{6})\b', address)
            search_value = postal_match.group(1) if postal_match else address

            # Step 1: Geocode address to get coordinates
            geo_response = requests.get(
                "https://www.onemap.gov.sg/api/common/elastic/search",
                params={
                    "searchVal": search_value,
                    "returnGeom": "Y",
                    "getAddrDetails": "Y",
                    "pageNum": 1
                },
                timeout=10
            )

            geo_data = geo_response.json()
            results = geo_data.get("results", [])
            if not results:
                logger.info(f"No geocoding results for: {search_value}")
                return None

            lat = results[0]["LATITUDE"]
            lon = results[0]["LONGITUDE"]

            # Step 2: Get planning area from coordinates
            pa_response = requests.get(
                "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea",
                params={"latitude": lat, "longitude": lon},
                headers={"Authorization": self._token},
                timeout=10
            )

            pa_data = pa_response.json()
            if pa_data and isinstance(pa_data, list) and pa_data[0].get("pln_area_n"):
                planning_area = pa_data[0]["pln_area_n"]
                logger.info(f"Planning area for '{search_value}': {planning_area}")
                return planning_area

        except Exception as e:
            logger.error(f"Planning area extraction error for '{address}': {e}")

        return None
