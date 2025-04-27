import firebase_admin
import sys
import pandas as pd
from firebase_admin import credentials
from firebase_admin import firestore
from dataset_worfklow.Main_scrape.extract_fields_from_scraped_text import TextExtract, SchemesStructuredOutput
from loguru import logger
import argparse
from datetime import datetime, timezone

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract fields from scraped text and update Firestore.')
    parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
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

        if fields_populated:
            logger.info(f"Skipping extraction for document {doc_id} as essential fields are already populated.")
            continue # Skip to the next document

        scraped_text = doc_data.get("scraped_text")
        if scraped_text:
            try:
                structured_output = text_extract.extract_text(scraped_text)
                structured_output_dict = structured_output.dict()
                keys_to_conditionally_update = {"who_is_it_for", "what_it_gives", "scheme_type", "search_booster"}
                updates = {} # Dictionary to hold updates
                for key, value in structured_output_dict.items():
                    should_update = True
                    # Conditionally update only if the key is in the specified set AND the existing value is missing or empty
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
                    doc_ref.update(updates)
                    logger.info(f"Updated document {doc_id} with keys: {', '.join(updates.keys())}")

            except Exception as e:
                logger.error(f"Error extracting text and updating document {doc_id}: {e}")
                keys = SchemesStructuredOutput.model_fields.keys()
                error_updates = {key: None for key in keys}
                doc_ref.update(error_updates) # Update with None for error cases

        else:
            # if no scraped text, continue to add empty fields to prevent NaNs in pandas
            logger.info(f"No scraped text found for document {doc_id}")
            keys = SchemesStructuredOutput.model_fields.keys()
            error_updates = {key: None for key in keys}
            doc_ref.update(error_updates) # Update with None for error cases

