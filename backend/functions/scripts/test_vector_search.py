"""
Test Firestore vector search on schemes_embeddings collection.

Search flow:
1. Query schemes_embeddings with findNearest() -> get doc_ids
2. Fetch full scheme data from schemes collection

Run against dev project after populating and creating the vector index.

Usage:
    cd backend/functions
    uv run python scripts/test_vector_search.py
"""

import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from langchain_openai import AzureOpenAIEmbeddings
from loguru import logger


# Load environment variables
load_dotenv()

COLLECTION_EMBEDDINGS = "schemes_embeddings"
COLLECTION_SCHEMES = "schemes"


def init_firebase():
    """Initialize Firebase connection."""
    private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": os.getenv("FB_TYPE"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI"),
            "token_uri": os.getenv("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        }
    )

    try:
        initialize_app(cred)
    except ValueError:
        pass  # Already initialized

    return firestore.client()


def init_embeddings():
    """Initialize Azure OpenAI embeddings (same config as searchModelManager.py)."""
    return AzureOpenAIEmbeddings(
        azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"],
        api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
        dimensions=2048,  # Firestore max is 2048
    )


def test_vector_search(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Test vector search with a query.

    Args:
        query: Search query text
        top_k: Number of results to return

    Returns:
        List of matching schemes with their data
    """
    db = init_firebase()
    embeddings = init_embeddings()

    # Step 1: Generate query embedding
    logger.info(f"Query: '{query}'")
    query_vector = embeddings.embed_query(query)
    logger.info(f"Generated embedding with {len(query_vector)} dimensions")

    # Step 2: Perform vector search on embeddings collection
    collection = db.collection(COLLECTION_EMBEDDINGS)
    vector_query = collection.find_nearest(
        vector_field="embedding",
        query_vector=Vector(query_vector),
        distance_measure=DistanceMeasure.COSINE,
        limit=top_k,
    )

    embedding_results = vector_query.get()
    doc_ids = [doc.id for doc in embedding_results]
    logger.info(f"Found {len(doc_ids)} matching embeddings")

    if not doc_ids:
        logger.warning("No results found")
        return []

    # Step 3: Fetch full scheme data from schemes collection
    schemes_data = []

    # Batch fetch in chunks of 30 (Firestore 'in' query limit)
    for i in range(0, len(doc_ids), 30):
        batch_ids = doc_ids[i : i + 30]
        docs = db.collection(COLLECTION_SCHEMES).where("__name__", "in", batch_ids).get()
        for doc in docs:
            scheme_data = doc.to_dict()
            scheme_data["scheme_id"] = doc.id
            schemes_data.append(scheme_data)

    # Sort results to match doc_ids order (findNearest returns sorted by distance)
    id_to_scheme = {s["scheme_id"]: s for s in schemes_data}
    ordered_schemes = [id_to_scheme[doc_id] for doc_id in doc_ids if doc_id in id_to_scheme]

    logger.info(f"\nTop {top_k} results for: '{query}'")
    logger.info("-" * 60)
    for i, scheme in enumerate(ordered_schemes, 1):
        scheme_name = scheme.get("scheme", "Unknown")
        agency = scheme.get("agency", "Unknown")
        logger.info(f"{i}. {scheme_name} ({agency})")

    return ordered_schemes


def count_embeddings() -> int:
    """Count documents in schemes_embeddings collection."""
    db = init_firebase()
    docs = db.collection(COLLECTION_EMBEDDINGS).stream()
    count = sum(1 for _ in docs)
    return count


if __name__ == "__main__":
    # Check if embeddings collection has data
    logger.info("Checking schemes_embeddings collection...")
    count = count_embeddings()
    logger.info(f"Found {count} embeddings in collection")

    if count == 0:
        logger.warning("No embeddings found. Run populate_embeddings.py first.")
        logger.warning("Also ensure the vector index has been created (see plan for gcloud command).")
        exit(1)

    # Test queries
    test_queries = [
        "financial assistance for elderly",
        "childcare subsidies for low income families",
        "mental health support",
        "job training for unemployed",
        "housing grants for first time buyers",
    ]

    for query in test_queries:
        print("\n" + "=" * 60)
        results = test_vector_search(query, top_k=5)
        print(f"Retrieved {len(results)} schemes")
