import json
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
import numpy as np
import faiss
import os
import spacy
import re
import argparse
import sys
from loguru import logger
from tqdm import tqdm  # Added tqdm for progress bar
from logging_config import ensure_logging_setup

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore



# Ensure logging is set up (will use existing setup if already initialized)
ensure_logging_setup()
logger.info("Logger initialised")

model_save_path = './models/schemesv2-torch-allmpp-model'
tokenizer_save_path = './models/schemesv2-torch-allmpp-tokenizer'
embeddings_save_name = './models/schemesv2-your_embeddings.npy'
index_save_name = './models/schemesv2-your_index.faiss'

# Global variables will be initialized in test_function

#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

# Now, you can use `index` for similarity searches with new user queries
def search_similar_items(query_text, full_query, model, tokenizer, index, index_to_scheme_id, db, top_k=10):

    # preproc = preprocessing(query_text)
    preproc = query_text
    # Compute embedding for the query text
    # query_embedding = model.encode([preproc])

    # Tokenize text
    encoded_input = tokenizer([preproc], padding=True, truncation=True, return_tensors='pt')

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Perform pooling
    query_embedding = mean_pooling(model_output, encoded_input['attention_mask'])

    # Normalize embeddings
    query_embedding = F.normalize(query_embedding, p=2, dim=1)

    query_embedding = np.array(query_embedding).astype('float32')

    # Perform the search
    distances, indices = index.search(query_embedding, top_k)
    similarity_scores =  np.exp(-distances)

    # Retrieve the scheme_ids using the FAISS indices
    retrieved_scheme_ids = [index_to_scheme_id[str(idx)] for idx in indices[0]]

    # Fetch scheme details from Firestore
    logger.info(f"Fetching details for {len(retrieved_scheme_ids)} schemes...")
    scheme_details = []
    # Added tqdm for progress bar
    for scheme_id in tqdm(retrieved_scheme_ids, desc="Fetching scheme details"):
        doc_ref = db.collection("schemes").document(scheme_id)
        doc = doc_ref.get()
        if doc.exists:
            scheme_details.append(doc.to_dict())
        else:
            logger.warning(f"Scheme ID {scheme_id} not found in Firestore.")
    logger.info("Scheme details fetched.")

    # Convert scheme details to a DataFrame
    scheme_df = pd.DataFrame(scheme_details)

    # Add similarity scores to the DataFrame
    results = pd.concat(
        [scheme_df.reset_index(drop=True), pd.DataFrame(similarity_scores[0], columns=['Similarity']).reset_index(drop=True)],
        axis=1
    )

    # Add the query to the results and sort by similarity
    results['query'] = full_query
    results = results.sort_values(['Similarity'], ascending=False)


    # similar_items = pd.DataFrame([df.iloc[indices[0]], distances[0], similarity_scores[0]])
    # Retrieve the most similar items
    #similar_items = df.iloc[indices[0]][['Scheme', 'Agency', 'Description']]

    #results = pd.concat([similar_items.reset_index(drop=True), pd.DataFrame(similarity_scores[0]).reset_index(drop=True)], axis=1)
    #results = results.set_axis(['Scheme', 'Agency', 'Description', 'Similarity'], axis=1)
    #results['query'] = full_query
    #results = results.sort_values(['Similarity'], ascending=False)

    return results



def combine_and_aggregate_results(needs, user_query, model, tokenizer, index, index_to_scheme_id, db):
    # DataFrame to store combined results
    combined_results = pd.DataFrame(columns=['scheme', 'agency', 'description', 'Similarity', 'query'])

    logger.info(f"Processing {len(needs)} identified needs...")
    # Process each need with tqdm progress bar
    for need in tqdm(needs, desc="Processing needs"):
        # Get the results for the current need
        logger.debug(f"Searching for need: {need}")
        current_results = search_similar_items(need, user_query, model, tokenizer, index, index_to_scheme_id, db)
        # Combine with the overall results
        combined_results = pd.concat([combined_results, current_results], ignore_index=True)
    logger.info("Finished processing needs.")

    # Handle duplicates: Aggregate similarity for duplicates and drop duplicates
    aggregated_results = combined_results.groupby(['scheme', 'agency', 'description', 'query'], as_index=False).agg({
        'Similarity': 'mean'  # Adjust this function as needed to aggregate similarity scores appropriately
    })

    # Sort by similarity in descending order
    sorted_results = aggregated_results.sort_values(by='Similarity', ascending=False).reset_index(drop=True)

    return sorted_results



def extract_needs_based_on_conjunctions(sentence, nlp):
    """Extract distinct needs based on coordinating conjunctions."""
    doc = nlp(sentence)
    needs = []
    current_need_tokens = []

    for token in doc:
        # If the token is a coordinating conjunction (e.g., 'and') and not at the start of the sentence,
        # consider the preceding tokens as one distinct need.
        if token.text.lower() in ['and', 'or'] and token.i != 0:
            if current_need_tokens:  # Ensure there's content before the conjunction
                needs.append(" ".join([t.text for t in current_need_tokens]))
                current_need_tokens = []  # Reset for the next need
        else:
            current_need_tokens.append(token)

    # Add the last accumulated tokens as a need, if any.
    if current_need_tokens:
        needs.append(" ".join([t.text for t in current_need_tokens]))

    return needs

def split_query_into_needs(query, nlp):
    """Split the query into sentences and then extract needs focusing on conjunctions."""
    sentences = split_into_sentences(query, nlp)
    all_needs = []
    for sentence in sentences:
        needs_in_sentence = extract_needs_based_on_conjunctions(sentence, nlp)
        all_needs.extend(needs_in_sentence)
    return all_needs

# Helper function to split the query into sentences
def split_into_sentences(text, nlp):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]


# Load spaCy English model
def preprocessing(sentence, nlp):
    # Text cleaning steps from spacy_tokenizer
    sentence = re.sub('\'', '', sentence)  # Remove distracting single quotes
    sentence = re.sub(' +', ' ', sentence)  # Replace extra spaces
    sentence = re.sub(r'\n: \'\'.*', '', sentence)  # Remove specific unwanted lines
    sentence = re.sub(r'\n!.*', '', sentence)
    sentence = re.sub(r'^:\'\'.*', '', sentence)
    sentence = re.sub(r'\n', ' ', sentence)  # Replace non-breaking new lines with space

    # Tokenization and further processing with spaCy
    doc = nlp(sentence)
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

def test_function(db):
    logger.info("Starting test function...")
    logger.info("Using provided Firebase database connection")

    # Load the FAISS index-to-scheme_id mapping
    logger.info("Loading FAISS index-to-scheme_id mapping...")
    with open('./models/index_to_scheme_id.json', 'r') as f:
        index_to_scheme_id = json.load(f)
    logger.info("Mapping loaded.")

    # Load model and tokenizer at startup
    logger.info("Loading model and tokenizer...")
    model = AutoModel.from_pretrained(model_save_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_save_path)
    logger.info("Model and tokenizer loaded.")

    # Load embeddings and FAISS index
    logger.info("Loading embeddings and FAISS index...")
    embeddings = np.load(embeddings_save_name)
    index = faiss.read_index(index_save_name)
    logger.info("Embeddings and index loaded.")

    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")

    query = "my client needs a blood pressure monitor"
    logger.info(f"Testing with query: {query}")
    distinct_needs = split_query_into_needs(query, nlp)
    logger.info(f"Distinct needs: {distinct_needs}")

    logger.info(f"Distinct needs preproc : {[preprocessing(x, nlp) for x in distinct_needs]}")

    user_query = "I am pregnant teen suffering from depression and family abuse"
    # user_query = "My client needs assistance as a dialysis patient. She is also in need of a job and financial support after COVID 19 has caused her to be retrenched"
    logger.info(f"Testing with user query: {user_query}")

    split_query = split_query_into_needs(user_query, nlp)
    # split_query = split_query_into_needs("I am a 31 year old married with one kid in need of more money")
    logger.info(f"Split query into needs: {split_query}")
    final_results = combine_and_aggregate_results(split_query, user_query, model, tokenizer, index, index_to_scheme_id, db)

    logger.info(f"Final aggregated results:\n{final_results}")
    logger.info("Test function completed successfully")

# if __name__ == "__main__":
    # Set up argument parser
    # parser = argparse.ArgumentParser(description='Test model artefacts and perform similarity search.')
    # parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
    # args = parser.parse_args()
    # test_function(args.creds_file)
