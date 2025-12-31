"""
Firestore embedding reindex utility.

Updates the schemes_embeddings collection with doc_id + embedding.
Original 'schemes' collection is unchanged.

This replaces reindex_chroma.py for Firestore Vector Search.
"""
import os
import time
from typing import Dict, Any

import pandas as pd
from firebase_admin import firestore
from google.cloud.firestore_v1.vector import Vector
from langchain_openai import AzureOpenAIEmbeddings
from loguru import logger

COLLECTION_SCHEMES = "schemes"
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


def reindex_embeddings(db=None) -> Dict[str, Any]:
    """
    Update schemes_embeddings collection with embeddings.

    Reads from 'schemes' collection, writes to 'schemes_embeddings' collection.
    Filters out inactive schemes.

    Args:
        db: Firestore client (optional, will create if not provided)

    Returns:
        dict with:
            - success: bool
            - total_schemes: int - total schemes in Firestore
            - indexed_schemes: int - schemes added to embeddings collection
            - skipped_inactive: int - inactive schemes filtered out
            - duration_seconds: float
            - error: str|None
    """
    start_time = time.time()

    try:
        logger.info("Starting Firestore embedding reindex...")

        if db is None:
            db = firestore.client()

        # Initialize embeddings model (same config as searchModelManager.py)
        # Use dimensions=2048 for text-embedding-3-large (Firestore max is 2048)
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"],
            api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
            model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
            dimensions=2048,
        )

        # Fetch all schemes from schemes collection
        logger.info(f"Fetching documents from '{COLLECTION_SCHEMES}'...")
        docs = db.collection(COLLECTION_SCHEMES).stream()
        schemes_list = [{**scheme.to_dict(), "doc_id": scheme.id} for scheme in docs]
        df = pd.DataFrame(schemes_list)
        total_schemes = len(df)
        logger.info(f"Retrieved {total_schemes} documents from Firestore")

        # Filter out inactive schemes (handles missing status field)
        initial_count = len(df)
        if "status" in df.columns:
            df = df[df["status"] != "inactive"]
        skipped_inactive = initial_count - len(df)

        if skipped_inactive > 0:
            logger.info(f"Filtered out {skipped_inactive} inactive schemes")

        if df.empty:
            return {
                "success": True,
                "total_schemes": total_schemes,
                "indexed_schemes": 0,
                "skipped_inactive": skipped_inactive,
                "duration_seconds": round(time.time() - start_time, 2),
                "error": "No active schemes to index"
            }

        # Build desc_booster field
        logger.info("Building desc_booster field...")
        df["desc_booster"] = df.apply(build_desc_booster, axis=1)

        # Log empty desc_booster rows
        empty_rows = df[df["desc_booster"].str.strip() == ""]
        if len(empty_rows) > 0:
            logger.warning(f"Found {len(empty_rows)} schemes with empty desc_booster")

        # Generate embeddings in batches and write to embeddings collection
        batch_size = 50  # Smaller batches for embedding API rate limits
        indexed = 0

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            texts = batch["desc_booster"].tolist()
            doc_ids = batch["doc_id"].tolist()

            # Generate embeddings for batch
            logger.info(f"Generating embeddings for batch {i//batch_size + 1}...")
            vectors = embeddings.embed_documents(texts)

            # Write to embeddings collection (only doc_id + embedding)
            batch_writer = db.batch()
            for doc_id, vector in zip(doc_ids, vectors):
                doc_ref = db.collection(COLLECTION_EMBEDDINGS).document(doc_id)
                batch_writer.set(doc_ref, {"embedding": Vector(vector)})

            batch_writer.commit()
            indexed += len(batch)
            logger.info(f"Indexed {indexed}/{len(df)} embeddings")

        duration = time.time() - start_time
        logger.info(
            f"Reindex completed in {duration:.2f}s "
            f"({indexed} schemes indexed, {skipped_inactive} inactive skipped)"
        )

        return {
            "success": True,
            "total_schemes": total_schemes,
            "indexed_schemes": indexed,
            "skipped_inactive": skipped_inactive,
            "duration_seconds": round(duration, 2),
            "error": None
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Embedding reindex failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "total_schemes": 0,
            "indexed_schemes": 0,
            "skipped_inactive": 0,
            "duration_seconds": round(duration, 2),
            "error": str(e)
        }
