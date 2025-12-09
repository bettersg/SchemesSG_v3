"""
Storage operations for Slack scraping errors using Firestore.

This module replaces CSV/JSON file operations with Firestore database operations.
Firestore collections:
- scrape_errors_source: Original scraped data
- scrape_errors_edits: Edited/reviewed data
- _config: Configuration data (notified_ids state)
"""
from typing import Dict, List, Optional, Set

from fb_manager.firebaseManager import FirebaseManager

# Firestore client instance
firebase_manager = FirebaseManager()

# Collection and document names
SOURCE_COLLECTION = "scrape_errors_source"
EDITS_COLLECTION = "scrape_errors_edits"
CONFIG_COLLECTION = "_config"
NOTIFIED_STATE_DOC_ID = "slack_notified_state"


def read_source_rows() -> List[Dict[str, str]]:
    """
    Read all source documents from Firestore collection.
    
    Returns:
        List of dictionaries with document data, each includes 'id' field from document ID.
    """
    collection = firebase_manager.firestore_client.collection(SOURCE_COLLECTION)
    docs = collection.stream()
    
    result = []
    for doc in docs:
        doc_data = doc.to_dict() or {}
        doc_data["id"] = doc.id
        result.append(doc_data)
    
    return result


def get_source_doc(doc_id: str) -> Optional[Dict[str, str]]:
    """
    Get a specific source document by ID.
    
    Args:
        doc_id: Document ID to retrieve
        
    Returns:
        Dictionary with document data including 'id' field, or None if not found
    """
    doc_ref = firebase_manager.firestore_client.collection(SOURCE_COLLECTION).document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        doc_data = doc.to_dict() or {}
        doc_data["id"] = doc.id
        return doc_data
    return None


def upsert_source_doc(doc_id: str, data: Dict[str, str]) -> Dict[str, str]:
    """
    Insert or update a source document in Firestore.
    
    Args:
        doc_id: Document ID
        data: Dictionary with fields: scheme_name, scheme_url, scraped_text
        
    Returns:
        Dictionary with merged document data including 'id' field
    """
    doc_ref = firebase_manager.firestore_client.collection(SOURCE_COLLECTION).document(doc_id)
    
    # Get existing document if it exists
    existing_doc = doc_ref.get()
    existing_data = existing_doc.to_dict() if existing_doc.exists else {}
    
    # Merge new data with existing data (new values override existing ones)
    merged_data = {
        "scheme_name": data.get("scheme_name", existing_data.get("scheme_name", "")),
        "scheme_url": data.get("scheme_url", existing_data.get("scheme_url", "")),
        "scraped_text": data.get("scraped_text", existing_data.get("scraped_text", "")),
    }
    
    # Use set with merge=True for upsert operation
    doc_ref.set(merged_data, merge=True)
    
    # Return data with id included
    merged_data["id"] = doc_id
    return merged_data


def upsert_edit_doc(doc_id: str, data: Dict[str, str]) -> Dict[str, str]:
    """
    Insert or update an edit document in Firestore.
    
    Args:
        doc_id: Document ID
        data: Dictionary with fields: scheme_name, scheme_url, scraped_text, 
              updated_at, updated_by
        
    Returns:
        Dictionary with merged document data including 'id' field
    """
    doc_ref = firebase_manager.firestore_client.collection(EDITS_COLLECTION).document(doc_id)
    
    # Get existing document if it exists
    existing_doc = doc_ref.get()
    existing_data = existing_doc.to_dict() if existing_doc.exists else {}
    
    # Merge new data with existing data
    merged_data = {**existing_data, **data}
    
    # Use set with merge=True for upsert operation
    doc_ref.set(merged_data, merge=True)
    
    # Return data with id included
    merged_data["id"] = doc_id
    return merged_data


def load_notified_ids() -> Set[str]:
    """
    Load the set of document IDs that have been notified to Slack.
    
    Returns:
        Set of document ID strings
    """
    doc_ref = firebase_manager.firestore_client.collection(CONFIG_COLLECTION).document(NOTIFIED_STATE_DOC_ID)
    doc = doc_ref.get()
    
    if doc.exists:
        doc_data = doc.to_dict() or {}
        notified_ids = doc_data.get("notified_ids", [])
        return set(notified_ids) if isinstance(notified_ids, list) else set()
    
    return set()


def save_notified_ids(ids: Set[str]) -> None:
    """
    Save the set of document IDs that have been notified to Slack.
    
    Args:
        ids: Set of document ID strings to save
    """
    doc_ref = firebase_manager.firestore_client.collection(CONFIG_COLLECTION).document(NOTIFIED_STATE_DOC_ID)
    
    # Convert set to sorted list for storage
    data = {
        "notified_ids": sorted(list(ids))
    }
    
    # Use set with merge=True to preserve other fields if they exist
    doc_ref.set(data, merge=True)

