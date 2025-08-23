import firebase_admin
import sys
from firebase_admin import credentials
from firebase_admin import firestore
from loguru import logger
import argparse
import requests
import re
from dotenv import dotenv_values, load_dotenv
import os


class Config:
    def __init__(self):
        load_dotenv("dataset_workflow/.env")

        for key, value in dotenv_values().items():
            setattr(self, key.lower(), value)

    def __getattr__(self, item):
        attr = os.getenv(item.upper())
        if attr:
            setattr(self, item.lower(), attr)
        return attr


def get_onemap_access_token(email, password):
    """
    Obtain OneMap access token using email and password.
    Returns the access token string or None if failed.
    """
    try:
        url = "https://www.onemap.gov.sg/api/auth/post/getToken"

        payload = {
            "email": email,
            "password": password
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            expiry_timestamp = data.get("expiry_timestamp")

            if access_token:
                logger.info(f"Successfully obtained OneMap access token. Expires at: {expiry_timestamp}")
                return access_token
            else:
                logger.error("No access_token found in response")
                return None
        else:
            logger.error(f"Failed to obtain OneMap access token. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error obtaining OneMap access token: {e}")
        return None


def extract_postal_code(address):
    """
    Extract 6-digit postal code from Singapore address string.
    Returns the postal code string or None if not found.
    """
    try:
        # Pattern to match 6-digit postal codes in Singapore addresses
        # Matches patterns like: 310005, Singapore 310005, etc.
        postal_pattern = r'\b(\d{6})\b'
        match = re.search(postal_pattern, address)

        if match:
            postal_code = match.group(1)
            logger.info(f"Extracted postal code: {postal_code} from address: {address}")
            return postal_code
        else:
            logger.warning(f"No postal code found in address: {address}")
            return None
    except Exception as e:
        logger.error(f"Error extracting postal code from address '{address}': {e}")
        return None


def extract_planning_area_from_address(address, token):
    """
    Given an address and OneMap API token, return the planning area name using OneMap public APIs.
    First tries to extract postal code and use it for search, falls back to full address if needed.
    """
    try:
        # First, try to extract postal code from the address
        postal_code = extract_postal_code(address)
        search_value = postal_code if postal_code else address

        logger.info(f"Using search value: {search_value} (postal code: {postal_code is not None})")

        # 1. Geocode
        params = {
            "searchVal": search_value,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1
        }
        geo_resp = requests.get("https://www.onemap.gov.sg/api/common/elastic/search", params=params, timeout=10)

        geo = geo_resp.json()
        results = geo.get("results", [])
        if not results:
            logger.error(f"No geocode results for search value: {search_value}")
            return None
        lat = results[0]["LATITUDE"]
        lon = results[0]["LONGITUDE"]

        # 2. Planning Area (public endpoint with Authorization header)
        pa_params = {"latitude": lat, "longitude": lon}
        headers = {"Authorization": token}
        pa_resp = requests.get(
            "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea",
            params=pa_params,
            headers=headers,
            timeout=10
        )

        pa = pa_resp.json()
        if not pa or not isinstance(pa, list) or not pa[0].get("pln_area_n"):
            logger.error(f"No planning area found for lat/lon: {lat}, {lon}")
            return None
        return pa[0]["pln_area_n"]
    except Exception as e:
        logger.error(f"Error in extract_planning_area_from_address: {e}")
        return None
    
def add_town_areas(creds_file):
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    logger.info("Logger initialised")

    # Initialize config and get OneMap credentials
    config = Config()
    onemap_email = config.ONEMAP_EMAIL
    onemap_password = config.ONEMAP_EMAIL_PASSWORD

    if not onemap_email or not onemap_password:
        logger.error("OneMap email or password not found in environment variables")
        sys.exit(1)

    # Obtain OneMap access token
    logger.info("Obtaining OneMap access token...")
    onemap_token = get_onemap_access_token(onemap_email, onemap_password)

    if not onemap_token:
        logger.error("Failed to obtain OneMap access token. Exiting.")
        sys.exit(1)

    cred = credentials.Certificate(creds_file)
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Get all documents from the collection
    docs = db.collection("schemes").stream()
    doc_ids = [doc.id for doc in docs]

    for doc_id in doc_ids:
        doc_ref = db.collection("schemes").document(doc_id)
        doc_snapshot = doc_ref.get()
        if not doc_snapshot.exists:
            logger.warning(f"Document {doc_id} not found.")
            continue
        doc_data = doc_snapshot.to_dict()
        update_time = doc_snapshot.update_time
        logger.info(f"Document {doc_id} - Last updated (metadata): {update_time}")

        address = doc_data.get("address")
        updates = {}

        # Check if planning_area is already present
        planning_area_already_present = doc_data.get("planning_area") is not None
        logger.info(f"Planning area already present for document {doc_id}, updating.")
        # if planning_area_already_present:
        #     logger.info(f"Planning area already present for document {doc_id}, skipping update.")
        #     continue

        # Generate planning area if address exists
        if address:
            try:
                # Handle both single address (string) and multiple addresses (array)
                if isinstance(address, list):
                    # Multiple addresses - generate planning area for each
                    planning_areas = []
                    for addr in address:
                        if addr:  # Check if address is not None or empty
                            planning_area = extract_planning_area_from_address(addr, onemap_token)
                            planning_areas.append(planning_area if planning_area else "No Location")
                        else:
                            planning_areas.append("No Location")
                    updates["planning_area"] = planning_areas
                    logger.info(f"Generated planning areas for document {doc_id} with {len(planning_areas)} addresses")
                else:
                    # Single address - generate planning area for the string
                    planning_area = extract_planning_area_from_address(address, onemap_token)
                    updates["planning_area"] = planning_area if planning_area else "No Location"
                    logger.info(f"Generated planning area for document {doc_id}")
            except Exception as e:
                logger.error(f"Error generating planning area for document {doc_id}: {e}")
                if isinstance(address, list):
                    updates["planning_area"] = ["No Location"] * len(address)
                else:
                    updates["planning_area"] = "No Location"
        else:
            logger.info(f"No address found for document {doc_id}, skipping planning area")
            updates["planning_area"] = "No Location"

        # Update Firestore
        if updates:
            doc_ref.update(updates)
            logger.info(f"Updated document {doc_id} with keys: {', '.join(updates.keys())}")
            logger.info(f"Updates: {updates}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate planning area for each scheme and update Firestore.')
    parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
    args = parser.parse_args()
    add_town_areas(args.creds_file)

    
