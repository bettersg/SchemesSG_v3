import firebase_admin
import sys
from firebase_admin import credentials
from firebase_admin import firestore
from dataset_worfklow.Main_scrape.extract_fields_from_scraped_text import TextExtract
from loguru import logger

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    logger.info("Logger initialised")
    cred = credentials.Certificate("backend/functions/creds.json")
    app = firebase_admin.initialize_app(cred)
    db = firestore.client()
    text_extract = TextExtract()
    # Get all documents from the collection
    docs = db.collection("schemes").stream()
    doc_ids = [doc.id for doc in docs]

    for doc_id in doc_ids:
        doc_ref = db.collection("schemes").document(doc_id)
        doc_data = doc_ref.get().to_dict()
        scraped_text = doc_data.get("scraped_text")
        if scraped_text:
            try:
                structured_output = text_extract.extract_text(scraped_text)
                doc_ref.update({"structured_output": structured_output.dict()})
                logger.info(f"Updated document {doc_id} with structured output")
            except Exception as e:
                logger.error(f"Error extracting text and updating document {doc_id}: {e}")
                raise e
        else:
            logger.info(f"No scraped text found for document {doc_id}")
