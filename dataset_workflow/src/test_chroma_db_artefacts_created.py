import os
import time
from pathlib import Path

import chromadb
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from loguru import logger

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


# Logging is already set up by the main pipeline
logger.info("Logger initialised")

parent_dir = Path(__file__).parent.parent
embeddings_path = parent_dir / "models" / "vector_store"


def test_chroma_pipeline(db):
    # Load environment variables
    load_dotenv()
    start = time.time()
    logger.info("Starting ChromaDB test pipeline...")

    # Connect to Chroma persistent store
    chroma_client = chromadb.PersistentClient(path=embeddings_path)

    collection = chroma_client.get_collection("schemes")
    logger.info("ChromaDB collection initialised")

    # Run a sample test query
    test_query = "financial support for single mothers"
    embedding_model = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"],
        api_version=os.environ["OPENAI_EMBEDDING_API_VERSION"],
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"],
    )
    logger.info(f"Running test query: '{test_query}'")

    result = collection.query(
        query_embeddings=[embedding_model.embed_query(test_query)], n_results=5
    )

    if not result or not result.get("ids"):
        logger.warning("No matching results found in ChromaDB.")
        return

    ids = result["ids"][0]
    distances = result.get("distances", [[0.0] * len(ids)])[0]
    similarities = [round(float(pow(2.71828, -d)), 5) for d in distances]

    logger.info(f"Top {len(ids)} results:")
    for scheme_id, score in zip(ids, similarities):
        logger.info(f"{scheme_id}  →  Similarity {score}")

    # Verify Firestore linkage
    logger.info("Fetching first few matched documents from Firestore...")
    fetched = []
    for scheme_id in ids[:3]:
        doc_ref = db.collection("schemes").document(scheme_id)
        doc = doc_ref.get()
        if doc.exists:
            fetched.append(doc.to_dict())
        else:
            logger.warning(f"Scheme {scheme_id} not found in Firestore")

    if fetched:
        df = pd.DataFrame(fetched)
        logger.info(f"Sample Firestore results:\n{df[['scheme', 'agency']].head(5)}")
    else:
        logger.warning("No Firestore documents fetched for these scheme IDs")

    elapsed = time.time() - start
    logger.success(f"Chroma pipeline test completed in {elapsed:.2f}s")
