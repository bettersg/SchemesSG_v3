"""
Populate schemes_embeddings collection for Firestore vector search.

Creates a separate collection with only doc_id + embedding.
Original 'schemes' collection is unchanged.

Run against dev project: schemessg-v3-dev

Usage:
    cd backend/functions
    uv run python scripts/populate_embeddings.py
"""
import os
import time
from typing import Dict, Any

import pandas as pd
from firebase_admin import firestore, credentials, initialize_app
from google.cloud.firestore_v1.vector import Vector
from langchain_openai import AzureOpenAIEmbeddings
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

COLLECTION_SOURCE = "schemes"
COLLECTION_EMBEDDINGS = "schemes_embeddings"


def build_desc_booster(row) -> str:
    """
    Build searchable description from scheme fields.

    Combines scheme name, agency, description, and categorization
    into a single searchable text field for vector embedding.
    """
    components = []
    for field in ["scheme", "agency", "llm_description", "search_booster",
                  "who_is_it_for", "what_it_gives", "scheme_type", "service_area"]:
        if pd.notna(row.get(field)):
            components.append(str(row[field]))
    return " ".join(components)


def populate_embeddings() -> Dict[str, Any]:
    """
    Create schemes_embeddings collection with doc_id + embedding only.

    Returns:
        dict with success, indexed_schemes, duration_seconds, error
    """
    start_time = time.time()

    try:
        # Initialize Firebase with credentials from environment
        private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
        cred = credentials.Certificate({
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
        })

        try:
            initialize_app(cred)
        except ValueError:
            pass  # Already initialized

        db = firestore.client()

        project_id = os.getenv("FB_PROJECT_ID")
        logger.info(f"Connected to project: {project_id}")

        # Initialize embeddings model (same as searchModelManager.py)
        # Use dimensions=2048 for text-embedding-3-large (Firestore max is 2048)
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"],
            api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
            model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
            dimensions=2048,
        )

        # Fetch all schemes from source collection
        logger.info(f"Fetching schemes from '{COLLECTION_SOURCE}'...")
        docs = db.collection(COLLECTION_SOURCE).stream()
        schemes = [{**doc.to_dict(), "doc_id": doc.id} for doc in docs]
        df = pd.DataFrame(schemes)

        # Filter out inactive schemes (handles missing status field)
        initial_count = len(df)
        if "status" in df.columns:
            df = df[df["status"] != "inactive"]
        skipped = initial_count - len(df)

        logger.info(f"Found {len(df)} active schemes (skipped {skipped} inactive)")

        if df.empty:
            return {
                "success": True,
                "indexed_schemes": 0,
                "duration_seconds": round(time.time() - start_time, 2),
                "error": "No active schemes found"
            }

        # Build desc_booster for embedding
        df["desc_booster"] = df.apply(build_desc_booster, axis=1)

        # Log empty desc_booster rows
        empty_rows = df[df["desc_booster"].str.strip() == ""]
        if len(empty_rows) > 0:
            logger.warning(f"Found {len(empty_rows)} schemes with empty desc_booster")

        # Generate embeddings and write to embeddings collection
        batch_size = 50  # Smaller batches for embedding API rate limits
        indexed = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            texts = batch["desc_booster"].tolist()
            doc_ids = batch["doc_id"].tolist()

            # Generate embeddings for batch
            logger.info(f"Generating embeddings for batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}...")
            vectors = embeddings.embed_documents(texts)

            # Write to embeddings collection (only doc_id + embedding)
            batch_writer = db.batch()
            for doc_id, vector in zip(doc_ids, vectors):
                doc_ref = db.collection(COLLECTION_EMBEDDINGS).document(doc_id)
                batch_writer.set(doc_ref, {"embedding": Vector(vector)})

            batch_writer.commit()
            indexed += len(batch)
            logger.info(f"Indexed {indexed}/{len(df)} embeddings to '{COLLECTION_EMBEDDINGS}'")

        duration = time.time() - start_time
        logger.info(f"Population completed in {duration:.2f}s ({indexed} embeddings)")

        return {
            "success": True,
            "indexed_schemes": indexed,
            "duration_seconds": round(duration, 2),
            "error": None
        }

    except Exception as e:
        logger.error(f"Population failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "indexed_schemes": 0,
            "duration_seconds": round(time.time() - start_time, 2),
            "error": str(e)
        }


if __name__ == "__main__":
    result = populate_embeddings()
    print(f"\nResult: {result}")
