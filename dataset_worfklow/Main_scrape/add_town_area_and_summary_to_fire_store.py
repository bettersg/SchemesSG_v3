import firebase_admin
import sys
from firebase_admin import credentials
from firebase_admin import firestore
from dataset_worfklow.Main_scrape.extract_fields_from_scraped_text import TextExtract
from loguru import logger
import argparse
import requests
import random


def extract_planning_area_from_address(address, token):
    """
    Given an address and OneMap API token, return the planning area name using OneMap public APIs.
    """
    try:
        # 1. Geocode
        params = {
            "searchVal": address,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1
        }
        geo_resp = requests.get("https://www.onemap.gov.sg/api/common/elastic/search", params=params, timeout=10)
        # logger.info(f"Geocode request URL: {geo_resp.url}")
        # logger.info(f"Geocode response status: {geo_resp.status_code}")
        # logger.info(f"Geocode response text: {geo_resp.text[:500]}")  # log first 500 chars

        geo = geo_resp.json()
        results = geo.get("results", [])
        if not results:
            logger.error(f"No geocode results for address: {address}")
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
        # logger.info(f"Planning area request URL: {pa_resp.url}")
        # logger.info(f"Planning area response status: {pa_resp.status_code}")
        # logger.info(f"Planning area response text: {pa_resp.text[:500]}")  # log first 500 chars

        pa = pa_resp.json()
        if not pa or not isinstance(pa, list) or not pa[0].get("pln_area_n"):
            logger.error(f"No planning area found for lat/lon: {lat}, {lon}")
            return None
        return pa[0]["pln_area_n"]
    except Exception as e:
        logger.error(f"Error in extract_planning_area_from_address: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate summary and planning area for each scheme and update Firestore.')
    parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
    parser.add_argument('--onemap_token', required=True, help='OneMap access token (required for public endpoint).')
    args = parser.parse_args()

    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    logger.info("Logger initialised")
    cred = credentials.Certificate(args.creds_file)
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    text_extract = TextExtract()
    # Get all documents from the collection
    docs = db.collection("schemes").stream()
    doc_ids = [doc.id for doc in docs]

    # --- For testing: fetch 5 random doc_ids where address is present ---
    # docs_with_address = db.collection("schemes").stream()
    # doc_ids_with_address = [doc.id for doc in docs_with_address if doc.to_dict().get("address")]
    # if len(doc_ids_with_address) > 5:
    #     sample_doc_ids_with_address = random.sample(doc_ids_with_address, 5)
    # else:
    #     sample_doc_ids_with_address = doc_ids_with_address
    # logger.info(f"Sample doc_ids with address: {sample_doc_ids_with_address}")
    # doc_ids = sample_doc_ids_with_address
    # --- End testing logic ---

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

        # Check if summary and planning_area are already present
        summary_already_present = doc_data.get("summary") is not None
        planning_area_already_present = doc_data.get("planning_area") is not None
        if summary_already_present and planning_area_already_present:
            logger.info(f"Both summary and planning area already present for document {doc_id}, skipping update.")
            continue

        # Check if summary already exists
        if summary_already_present:
            logger.info(f"Summary already present for document {doc_id}, skipping generation.")
            updates["summary"] = doc_data["summary"]
        else:
            # Generate summary
            # Concatenate all fields except 'id' into a single string
            concat_text = ""
            try:
                concat_text = "\n".join([
                    f"{k}: {v}" for k, v in doc_data.items() if k != "id" and k != "scraped_text" and v is not None
                ])
            except Exception as e:
                logger.error(f"Error concatenating fields for document {doc_id}: {e}")
                concat_text = None

            if concat_text:
                try:
                    summary = text_extract.generate_summary(concat_text)
                    updates["summary"] = summary
                    logger.info(f"Generated summary for document {doc_id}")
                except Exception as e:
                    logger.error(f"Error generating summary for document {doc_id}: {e}")
                    updates["summary"] = None
            else:
                logger.info(f"No valid fields found for document {doc_id}, setting summary to None")
                updates["summary"] = None

        # Check if planning_area already exists
        if planning_area_already_present:
            logger.info(f"Planning area already present for document {doc_id}, skipping generation.")
            updates["planning_area"] = doc_data["planning_area"]
        elif address:
            try:
                planning_area = extract_planning_area_from_address(address, args.onemap_token)
                updates["planning_area"] = planning_area
                logger.info(f"Generated planning area for document {doc_id}")
            except Exception as e:
                logger.error(f"Error generating planning area for document {doc_id}: {e}")
                updates["planning_area"] = None
        else:
            logger.info(f"No address found for document {doc_id}, skipping planning area")
            updates["planning_area"] = None

        # Update Firestore
        if updates:
            doc_ref.update(updates)
            logger.info(f"Updated document {doc_id} with keys: {', '.join(updates.keys())}")
            logger.info(f"Updates: {updates}")
