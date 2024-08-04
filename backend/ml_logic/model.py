import numpy as np
import torch
import torch.nn.functional as F
import pandas as pd

df = pd.read_csv("ml_logic/schemes-updated-with-text.csv")
print('got the df')



#Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


# Now, you can use `index` for similarity searches with new user queries
def search_similar_items(query_text, ml_models, full_query, top_k):
    model = ml_models["model"]
    tokenizer = ml_models["tokenizer"]
    embeddings = ml_models["embeddings"]
    index = ml_models["index"]

    preproc = query_text
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
    # similar_items = pd.DataFrame([df.iloc[indices[0]], distances[0], similarity_scores[0]])
    # Retrieve the most similar items
    similar_items = df.iloc[indices[0]][['Scheme', 'Agency', 'Description', 'Image', 'Link', 'Scraped Text', 'What it gives', 'Scheme Type']]

    results = pd.concat([similar_items.reset_index(drop=True), pd.DataFrame(similarity_scores[0]).reset_index(drop=True)], axis=1)
    results = results.set_axis(['Scheme', 'Agency', 'Description', 'Image', 'Link', 'Scraped Text', 'What it gives', 'Scheme Type', 'Similarity'], axis=1)
    results['query'] = full_query

    results = results.sort_values(['Similarity'], ascending=False)

    return results


def combine_and_aggregate_results(needs, ml_model, full_query, top_k, similarity_threshold):
    # DataFrame to store combined results
    combined_results = pd.DataFrame(columns=['Scheme', 'Agency', 'Description', 'Image', 'Link', 'Scraped Text', 'What it gives', 'Scheme Type', 'Similarity', 'query'])

    # Process each need
    for need in needs:
        # Get the results for the current need
        current_results = search_similar_items(need, ml_model, full_query, top_k)
        # Combine with the overall results
        combined_results = pd.concat([combined_results, current_results], ignore_index=True)

    # Handle duplicates: Aggregate similarity for duplicates and drop duplicates
    aggregated_results = combined_results.groupby(['Scheme', 'Agency', 'Description', 'Image', 'Link', 'Scraped Text', 'What it gives', 'Scheme Type', 'query'], as_index=False).agg({
        'Similarity': 'sum'  # Adjust this function as needed to aggregate similarity scores appropriately
    })

    # Calculate quintile thresholds
    quintile_thresholds = np.percentile(aggregated_results['Similarity'], [0, 20, 40, 60, 80, 100])
    # Assign quintile categories (0, 1, 2, 3, 4)
    # Since there are 5 thresholds (including 100th percentile), we specify 4 bins; pandas cuts into bins-1 categories
    aggregated_results['Quintile'] = pd.cut(aggregated_results['Similarity'], quintile_thresholds, labels=[0, 1, 2, 3, 4], include_lowest=True)

    #TODO add mental health model and increase the Similarity score

    # Filter out results that are below the minimum quintile threshold
    aggregated_results = aggregated_results[aggregated_results['Quintile'].astype(int) >= similarity_threshold]

    # Sort by similarity in descending order
    sorted_results = aggregated_results.sort_values(by='Similarity', ascending=False).reset_index(drop=True)

    return sorted_results
