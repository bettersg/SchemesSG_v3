# Setup
import os
import json
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import firebase_admin
import spacy
import re
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
import faiss
import numpy as np
from loguru import logger
import argparse # Import argparse

NLP = spacy.load("en_core_web_sm")

def preprocessing(sentence):
    # Text cleaning steps from spacy_tokenizer
    sentence = re.sub('\'', '', sentence)  # Remove distracting single quotes
    sentence = re.sub(' +', ' ', sentence)  # Replace extra spaces
    sentence = re.sub(r'\n: \'\'.*', '', sentence)  # Remove specific unwanted lines
    sentence = re.sub(r'\n!.*', '', sentence)
    sentence = re.sub(r'^:\'\'.*', '', sentence)
    sentence = re.sub(r'\n', ' ', sentence)  # Replace non-breaking new lines with space

    # Tokenization and further processing with spaCy
    doc = NLP(sentence)
    tokens = []
    for token in doc:
        # Check if the token is a stopword or punctuation
        if token.is_stop or token.is_punct:
            continue
        # Check for numeric tokens or tokens longer than 2 characters
        if token.like_num or len(token.text) > 2:
            # Lemmatize (handling pronouns) and apply lowercase
            lemma = token.lemma_.lower().strip() if token.lemma_ != "-PRON-" else token.lower_
            tokens.append(lemma)

    # Further clean up to remove any introduced extra spaces
    processed_text = ' '.join(tokens)
    processed_text = re.sub(' +', ' ', processed_text)

    return processed_text

def build_desc_booster(row):
    components = []

    # Check each column and add non-null values
    if pd.notna(row['scheme']):
        components.append(str(row['scheme']))
    if pd.notna(row['agency']):
        components.append(str(row['agency']))
    if pd.notna(row['llm_description']):
        components.append(str(row['llm_description']))
    if pd.notna(row['search_booster']):
        components.append(str(row['search_booster']))
    if pd.notna(row["who_is_it_for"]):
        components.append(str(row["who_is_it_for"]))
    if pd.notna(row['what_it_gives']):
        components.append(str(row['what_it_gives']))
    if pd.notna(row['scheme_type']):
        components.append(str(row['scheme_type']))
    if pd.notna(row['service_area']):
        components.append(str(row['service_area']))

    # Join all non-null components with spaces
    return ' '.join(components)

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def create_transformer_models(db):
    import time
    start_time = time.time()

    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )

    logger.info("Starting create_transformer_models process...")
    logger.info("Using provided Firebase database connection")

    # Get all documents from the collection
    logger.info("Fetching documents from Firestore...")
    docs = db.collection("schemes").stream()
    schemes_df = pd.DataFrame([{**scheme.to_dict(), "scheme_id": scheme.id} for scheme in docs])
    df = schemes_df
    logger.info(f"Retrieved {len(df)} documents from Firestore")

    logger.info("Building desc_booster field...")
    df['desc_booster'] = df.apply(build_desc_booster, axis=1)

    # Get rows where desc_booster is NA
    na_rows = df[df['desc_booster'].isna()]
    logger.info(f"Found {len(na_rows)} rows where desc_booster is NA")
    if len(na_rows) > 0:
        logger.warning("Full rows where desc_booster is NA:")
        print(na_rows)

    logger.info("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
    model = AutoModel.from_pretrained('sentence-transformers/all-mpnet-base-v2')
    logger.info("Tokenizer and model loaded successfully")

    # Process in batches to avoid memory issues
    batch_size = 32  # Adjust based on your memory constraints
    total_docs = len(df)
    logger.info(f"Processing {total_docs} documents in batches of {batch_size}")

    all_embeddings = []

    for i in range(0, total_docs, batch_size):
        batch_start = i
        batch_end = min(i + batch_size, total_docs)
        batch_docs = df.iloc[batch_start:batch_end]

        logger.info(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} (documents {batch_start}-{batch_end-1})")

        # Tokenize current batch
        batch_texts = batch_docs['desc_booster'].tolist()
        logger.info(f"Tokenizing batch of {len(batch_texts)} documents...")
        encoded_input = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='pt')

        # Compute token embeddings for current batch
        logger.info(f"Computing embeddings for batch...")
        with torch.no_grad():
            model_output = model(**encoded_input)

        # Perform pooling
        logger.info(f"Performing mean pooling for batch...")
        sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

        # Normalize embeddings
        sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)

        # Convert to numpy and add to all_embeddings
        batch_embeddings = sentence_embeddings.cpu().numpy().astype('float32')
        all_embeddings.append(batch_embeddings)

        logger.info(f"Completed batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")

        # Clear GPU memory if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Concatenate all embeddings
    logger.info("Concatenating all batch embeddings...")
    embeddings = np.vstack(all_embeddings)
    logger.info(f"Final embeddings shape: {embeddings.shape}")

    # Create a FAISS index
    logger.info("Creating FAISS index...")
    dimension = embeddings.shape[1]  # Dimension of the embeddings
    index = faiss.IndexFlatL2(dimension)  # Using the L2 distance for similarity
    index.add(embeddings)
    logger.info("FAISS index created and populated")

    # Create a mapping between FAISS index and `scheme_id`
    index_to_scheme_id = dict(enumerate(df['scheme_id']))
    logger.info(f"Created index mapping for {len(index_to_scheme_id)} schemes")

    # Create models directory - use relative path from current working directory
    # The script is run from dataset_workflow directory, so models will be in dataset_workflow/models
    models_dir = 'models'
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Created models directory: {os.path.abspath(models_dir)}")

    # Save index mapping
    index_mapping_path = os.path.join(models_dir, 'index_to_scheme_id.json')
    with open(index_mapping_path, 'w') as f:
        json.dump(index_to_scheme_id, f)
    logger.info(f"Index to scheme id saved to {os.path.abspath(index_mapping_path)}")

    # Define save paths - all relative to current working directory
    model_save_path = os.path.join(models_dir, 'schemesv2-torch-allmpp-model')
    tokenizer_save_path = os.path.join(models_dir, 'schemesv2-torch-allmpp-tokenizer')
    embeddings_save_name = os.path.join(models_dir, 'schemesv2-your_embeddings.npy')
    index_save_name = os.path.join(models_dir, 'schemesv2-your_index.faiss')

    # Save the embeddings and index to disk
    logger.info("Saving embeddings...")
    np.save(embeddings_save_name, embeddings)
    logger.info(f"Embeddings saved to {os.path.abspath(embeddings_save_name)}")

    logger.info("Saving FAISS index...")
    faiss.write_index(index, index_save_name)
    logger.info(f"Index saved to {os.path.abspath(index_save_name)}")

    # Save model
    logger.info("Saving model...")
    model.save_pretrained(model_save_path)
    logger.info(f"Model saved to {os.path.abspath(model_save_path)}")

    # Save tokenizer
    logger.info("Saving tokenizer...")
    tokenizer.save_pretrained(tokenizer_save_path)
    logger.info(f"Tokenizer saved to {os.path.abspath(tokenizer_save_path)}")

    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Process completed successfully in {total_time:.2f} seconds ({total_time/60:.2f} minutes)")


# if __name__ == "__main__":
#     # Set up argument parser
#     parser = argparse.ArgumentParser(description='Create transformer models and FAISS index.')
#     parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
#     args = parser.parse_args()

#     create_transformer_models(args.creds_file)
