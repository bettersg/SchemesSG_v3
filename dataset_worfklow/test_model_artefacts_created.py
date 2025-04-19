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

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


model_save_path = './models/schemesv2-torch-allmpp-model'
tokenizer_save_path = './models/schemesv2-torch-allmpp-tokenizer'
embeddings_save_name = './models/schemesv2-your_embeddings.npy'
index_save_name = './models/schemesv2-your_index.faiss'

# Use a service account to connect to firestore.
cred = credentials.Certificate("backend/functions/creds.json")
nlp = spacy.load("en_core_web_sm")

app = firebase_admin.initialize_app(cred)

db = firestore.client()
# Load the FAISS index-to-scheme_id mapping
with open('./models/index_to_scheme_id.json', 'r') as f:
    index_to_scheme_id = json.load(f)

# Load model and tokenizer at startup
model = AutoModel.from_pretrained(model_save_path)
tokenizer = AutoTokenizer.from_pretrained(tokenizer_save_path)

# Load the embeddings and index
embeddings = np.load(embeddings_save_name)
index = faiss.read_index(index_save_name)

#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

# Now, you can use `index` for similarity searches with new user queries
def search_similar_items(query_text, full_query, top_k=10):

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
    scheme_details = []
    for scheme_id in retrieved_scheme_ids:
        doc_ref = db.collection("schemes").document(scheme_id)
        doc = doc_ref.get()
        if doc.exists:
            scheme_details.append(doc.to_dict())

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



def combine_and_aggregate_results(needs, user_query):
    # DataFrame to store combined results
    combined_results = pd.DataFrame(columns=['Scheme', 'Agency', 'Description', 'Similarity', 'query'])

    # Process each need
    for need in needs:
        # Get the results for the current need
        current_results = search_similar_items(need, user_query)
        # Combine with the overall results
        combined_results = pd.concat([combined_results, current_results], ignore_index=True)

    # Handle duplicates: Aggregate similarity for duplicates and drop duplicates
    aggregated_results = combined_results.groupby(['Scheme', 'Agency', 'Description', 'query'], as_index=False).agg({
        'Similarity': 'mean'  # Adjust this function as needed to aggregate similarity scores appropriately
    })

    # Sort by similarity in descending order
    sorted_results = aggregated_results.sort_values(by='Similarity', ascending=False).reset_index(drop=True)

    return sorted_results



def extract_needs_based_on_conjunctions(sentence):
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

def split_query_into_needs(query):
    """Split the query into sentences and then extract needs focusing on conjunctions."""
    sentences = split_into_sentences(query)
    all_needs = []
    for sentence in sentences:
        needs_in_sentence = extract_needs_based_on_conjunctions(sentence)
        all_needs.extend(needs_in_sentence)
    return all_needs

# Helper function to split the query into sentences
def split_into_sentences(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]


# Load spaCy English model
def preprocessing(sentence):
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

def test_function():
    query = "my client needs a blood pressure monitor"
    distinct_needs = split_query_into_needs(query)
    print(f"Distinct needs: {distinct_needs}")

    print(f"Distinct needs preproc : {[preprocessing(x) for x in distinct_needs]}")
    user_query = "I am pregnant teen suffering from depression and family abuse"
    # user_query = "My client needs assistance as a dialysis patient. She is also in need of a job and financial support after COVID 19 has caused her to be retrenched"

    split_query = split_query_into_needs(user_query)
    # split_query = split_query_into_needs("I am a 31 year old married with one kid in need of more money")
    print(split_query)
    final_results = combine_and_aggregate_results(split_query, user_query)

    print(final_results)

test_function()