# Setup
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import chromadb
import pandas as pd
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from loguru import logger

# Logging is handled by the main pipeline


def build_desc_booster(row):
    components = []

    # Check each column and add non-null values
    if pd.notna(row["scheme"]):
        components.append(str(row["scheme"]))
    if pd.notna(row["agency"]):
        components.append(str(row["agency"]))
    if pd.notna(row["llm_description"]):
        components.append(str(row["llm_description"]))
    if pd.notna(row["search_booster"]):
        components.append(str(row["search_booster"]))
    if pd.notna(row["who_is_it_for"]):
        components.append(str(row["who_is_it_for"]))
    if pd.notna(row["what_it_gives"]):
        components.append(str(row["what_it_gives"]))
    if pd.notna(row["scheme_type"]):
        components.append(str(row["scheme_type"]))
    if pd.notna(row["service_area"]):
        components.append(str(row["service_area"]))

    # Join all non-null components with spaces
    return " ".join(components)


def create_chroma_db_artefacts(db):
    import time

    load_dotenv()
    start_time = time.time()

    logger.info("Starting create_chroma_db_artefacts process...")
    logger.info("Using provided Firebase database connection")

    # Get all documents from collection
    logger.info("Fetching documents from Firestore...")
    docs = db.collection("schemes").stream()
    schemes_df = pd.DataFrame(
        [{**scheme.to_dict(), "scheme_id": scheme.id} for scheme in docs]
    )
    df = schemes_df
    logger.info(f"Retrieved {len(df)} documents from Firestore")

    logger.info("Building desc_booster field...")
    df["desc_booster"] = df.apply(build_desc_booster, axis=1)

    # Get rows where desc_booster is NA
    na_rows = df[df["desc_booster"].isna()]
    logger.info(f"Found {len(na_rows)} rows where desc_booster is NA")
    if len(na_rows) > 0:
        logger.warning("Full rows where desc_booster is NA:")
        print(na_rows)

    # Create persistence ChromaDB vector store
    logger.info("Creating ChromaDB vector store...")
    chroma_dir = "models/vector_store"
    if not os.path.exists(chroma_dir):
        os.makedirs(chroma_dir)
        logger.info(f"Created directory {chroma_dir}")
    client = chromadb.PersistentClient(path=chroma_dir)
    # Ensure collection names aligned with searchModelManager's usage of vector collection
    collection = client.create_collection(
        name="schemes",
        embedding_function=OpenAIEmbeddingFunction(
            api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
            api_base=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
            api_version=os.getenv("OPENAI_EMBEDDING_API_VERSION"),
            api_type="azure",
            deployment_id=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        ),
        configuration={"hnsw": {"space": "cosine"}},
    )

    scheme_ids = df["scheme_id"].tolist()
    descriptions = df["desc_booster"].tolist()

    logger.info("Adding documents to ChromaDB...")
    collection.add(ids=scheme_ids, documents=descriptions)

    end_time = time.time()
    total_time = end_time - start_time
    logger.info(
        f"Process completed successfully in {total_time:.2f} seconds ({total_time / 60:.2f} minutes)"
    )
