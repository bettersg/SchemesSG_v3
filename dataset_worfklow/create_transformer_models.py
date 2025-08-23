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

def create_transformer_models(creds_file):
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    # Use a service account to connect to firestore.
    cred = credentials.Certificate(creds_file) # Use the path from arguments

    app = firebase_admin.initialize_app(cred)

    db = firestore.client()

    # Get all documents from the collection
    docs = db.collection("schemes").stream()
    schemes_df = pd.DataFrame([{**scheme.to_dict(), "scheme_id": scheme.id} for scheme in docs])
    df = schemes_df
    df['desc_booster'] = df.apply(build_desc_booster, axis=1)
    # Get rows where desc_booster is NA
    na_rows = df[df['desc_booster'].isna()]
    print("Full rows where desc_booster is NA:")

    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-mpnet-base-v2')
    model = AutoModel.from_pretrained('sentence-transformers/all-mpnet-base-v2')

    # Tokenize sentences
    encoded_input = tokenizer(df['desc_booster'].tolist(), padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    embeddings = sentence_embeddings
    # Convert embeddings to np.float32 as required by FAISS
    embeddings = np.array(embeddings).astype('float32')

    # Create a FAISS index
    dimension = embeddings.shape[1]  # Dimension of the embeddings
    index = faiss.IndexFlatL2(dimension)  # Using the L2 distance for similarity
    index.add(embeddings)
    # Create a mapping between FAISS index and `scheme_id`
    index_to_scheme_id = dict(enumerate(df['scheme_id']))


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Create transformer models and FAISS index.')
    parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
    args = parser.parse_args()

    create_transformer_models(args.creds_file)