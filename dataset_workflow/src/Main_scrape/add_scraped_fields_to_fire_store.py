import firebase_admin
import sys
from firebase_admin import credentials
from firebase_admin import firestore
from .utils import check_if_scraped_require_refresh
from src.Main_scrape.extract_fields_from_scraped_text import TextExtract, SchemesStructuredOutput
from loguru import logger
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
# Logging is handled by the main pipeline

def is_valid_scraped_text(scraped_text):
    """
    Check if scraped_text is valid for processing.
    Returns False if text is None, empty, too short, or contains error indicators.
    """
    if not scraped_text:
        return False

    # Convert to string if it's not already
    scraped_text_str = str(scraped_text).strip()

    # Check if empty or too short (less than 50 characters)
    if len(scraped_text_str) < 50:
        return False

    # Check for error indicators
    error_indicators = ['ERROR', 'HTTP Error', 'HTTP error', 'http error', 'error']
    if any(indicator in scraped_text_str for indicator in error_indicators):
        return False

    return True


def add_scraped_fields_to_fire_store(db, doc_ids=None):
    # Logging is already set up by the main pipeline
    logger.info("Logger initialised")
    text_extract = TextExtract()
    # Get documents to process
    if doc_ids is None or len(doc_ids)==0:
        # Get all documents from the collection
        docs = db.collection("schemes").stream()
        doc_ids = [doc.id for doc in docs]
    else:
        # Use provided doc_ids, ensuring they are strings
        doc_ids = [str(doc_id) for doc_id in doc_ids]
        logger.info(f"Processing specific doc_ids: {doc_ids}")

    for doc_id in doc_ids:
        doc_ref = db.collection("schemes").document(doc_id)
        doc_snapshot = doc_ref.get() # Get the snapshot object
        if not doc_snapshot.exists:
            logger.warning(f"Document {doc_id} not found.")
            continue
        doc_data = doc_snapshot.to_dict() # Get data from snapshot
        update_time = doc_snapshot.update_time # Get update time from snapshot metadata

        # Log the document's last update time from metadata
        logger.info(f"Document {doc_id} - Last updated (metadata): {update_time}")

        # Check if essential fields are already populated
        essential_fields = ["llm_description"] # User changed this
        fields_populated = all(doc_data.get(field) for field in essential_fields)

        # last scraped updated
        last_llm_processed_update = doc_data.get("last_llm_processed_update")
        require_refresh = check_if_scraped_require_refresh(last_llm_processed_update)


        if fields_populated and not require_refresh:
            logger.info(f"Skipping extraction for document {doc_id} as essential fields are already populated.")
            continue # Skip to the next document

        scraped_text = doc_data.get("scraped_text")
        description = doc_data.get("description")

        # Check if scraped_text is valid, if not use description as fallback
        if is_valid_scraped_text(scraped_text):
            text_to_process = scraped_text
            logger.info(f"Using scraped_text for document {doc_id}")
        elif description:
            text_to_process = description
            logger.info(f"Using description as fallback for document {doc_id} (scraped_text was invalid)")
        else:
            text_to_process = None
            logger.info(f"No valid text found for document {doc_id} (neither scraped_text nor description)")

        if text_to_process:
            try:

                structured_output = text_extract.extract_text(text_to_process)

                # Transform physical locations to database format
                db_format = text_extract.transform_to_database_format(structured_output)

                # Create the final structured output dict with transformed location data
                structured_output_dict = structured_output.dict()

                # Replace physical_locations with the transformed address, phone, email fields
                structured_output_dict.pop('physical_locations', None)  # Remove the original field
                structured_output_dict.update(db_format)  # Add the transformed fields

                keys_to_conditionally_update = {"who_is_it_for", "what_it_gives", "scheme_type", "search_booster"}
                updates = {} # Dictionary to hold updates
                for key, value in structured_output_dict.items():
                    should_update = True
                    # Conditionally update only if the key is in the specified set AND the existing value is missing or empty
                    # TODO Skip checks for conditional update for testing
                    if key in keys_to_conditionally_update:
                        existing_value = doc_data.get(key)
                        if existing_value:  # Checks if value exists and is not None, empty string, empty list, etc.
                            should_update = False
                            logger.info(f"Skipping update for key '{key}' in document {doc_id} as it already has value: {existing_value}")

                    if should_update:
                        # Add the update to the dictionary
                        updates[key] = value

                # Perform a single update operation if there are any changes
                if updates:
                    updates["last_llm_processed_update"] = SERVER_TIMESTAMP
                    logger.info(f"Added 'last_llm_processed_update' field to update_data for doc {doc_ref.id}")

                    doc_ref.update(updates)
                    logger.info(f"Updated document {doc_id} with keys: {', '.join(updates.keys())}")

            except Exception as e:
                logger.error(f"Error extracting text and updating document {doc_id}: {e}")
                # Create error updates with the expected fields including address, phone, email
                error_updates = {
                    'address': None,
                    'phone': None,
                    'email': None,
                    'llm_description': None,
                    'eligibility': None,
                    'how_to_apply': None,
                    'who_is_it_for': None,
                    'what_it_gives': None,
                    'scheme_type': None,
                    'search_booster': None,
                    'summary': None,
                    'service_area': None
                }
                doc_ref.update(error_updates) # Update with None for error cases

        else:
            # if no valid text found, continue to add empty fields to prevent NaNs in pandas
            logger.info(f"No valid text found for document {doc_id}")
            # Create empty updates with the expected fields including address, phone, email
            error_updates = {
                'address': None,
                'phone': None,
                'email': None,
                'llm_description': None,
                'eligibility': None,
                'how_to_apply': None,
                'who_is_it_for': None,
                'what_it_gives': None,
                'scheme_type': None,
                'search_booster': None,
                'summary': None,
                'service_area': None
            }
            doc_ref.update(error_updates) # Update with None for error cases


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Extract fields from scraped text and update Firestore.')
#     parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
#     args = parser.parse_args()

#     add_scraped_fields_to_fire_store(args.creds_file)
