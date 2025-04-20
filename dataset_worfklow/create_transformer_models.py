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
    if pd.notna(row['Scheme']):
        components.append(str(row['Scheme']))
    if pd.notna(row['Agency']):
        components.append(str(row['Agency']))
    if pd.notna(row['Description']):
        components.append(str(row['Description']))
    if pd.notna(row['search_booster(WL)']):
        components.append(str(row['search_booster(WL)']))
    if pd.notna(row["Who's it for"]):
        components.append(str(row["Who's it for"]))
    if pd.notna(row['What it gives']):
        components.append(str(row['What it gives']))
    if pd.notna(row['Scheme Type']):
        components.append(str(row['Scheme Type']))

    # Join all non-null components with spaces
    return ' '.join(components)

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )
    # Use a service account to connect to firestore.
    cred = credentials.Certificate("backend/functions/creds.json")

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



    # Assuming `model` is your PyTorch model and `tokenizer` is the Hugging Face tokenizer
    if not os.path.exists('./models'):
        os.makedirs('./models')

    with open('./models/index_to_scheme_id.json', 'w') as f:
        json.dump(index_to_scheme_id, f)
        logger.info("Index to scheme id saved")

    model_save_path = './models/schemesv2-torch-allmpp-model'
    tokenizer_save_path = './models/schemesv2-torch-allmpp-tokenizer'
    embeddings_save_name = './models/schemesv2-your_embeddings.npy'
    index_save_name = './models/schemesv2-your_index.faiss'


    # Save the embeddings and index to disk
    np.save(embeddings_save_name, embeddings)
    logger.info("Embeddings saved")
    faiss.write_index(index, index_save_name)
    logger.info("Index saved")
    # Save model
    model.save_pretrained(model_save_path)
    logger.info("Model saved")
    # Save tokenizer
    tokenizer.save_pretrained(tokenizer_save_path)
    logger.info("Tokenizer saved")


