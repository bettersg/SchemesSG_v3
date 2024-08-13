#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pickle
from collections import Counter
import json
import numpy as np
import pandas as pd
# from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
import re
from string import punctuation
from spellchecker import SpellChecker
from sklearn.metrics.pairwise import pairwise_distances

df = pd.read_csv('df.csv')
# with open('embeddings.pkl', 'rb') as handle:
#     emb = pickle.load(handle)
# biencoder = SentenceTransformer('paraphrase-distilroberta-base-v2')
crossencoder = CrossEncoder('crossencoder.pt')

spell = SpellChecker()
# Add words to vocabulary. Can continue adding as new queries come in, but would advise not to go too far; may inadvertently generate a lot of false positives
add = ['msf', 'sso', 'comcare', 'nkf', 'declutter', 'kikuchi', 'covid', 'covid-19', 'covid19', 'serangoon', 'sengkang', 'hougang', 'sinda', 'bukit', 'panjang', 'ubi',
       'taman', 'jurong', 'yishun', '4d']
spell.word_frequency.load_words(add)

def autocorrect(text):
    '''Mostly works if only 1 character was wrong. Wall time is 160 - 170ms
    Cannot autocorrect words with punctuation in between (mostly typos in contractions, e.g. "havn't").
    Singaporean/ethnic words/names may be autocorrected into something else; medical terms may be corrected insensitively, e.g. "Kikuchi" into "kimchi"
    If text was autocorrected, function returns a tuple. Else, returns None'''

    tokens = text.split()
    corrected_text = ''
    correction = False

    for i, word in enumerate(tokens):
        # Sadly spellchecker strips punctuation away, so strip them first, then insert back after spellchecking
        punctuation_front = punctuation_back = ''
        while word[-1] in punctuation:
            punctuation_back = word[-1] + punctuation_back
            word = word[:-1]

        while word[0] in punctuation:
            punctuation_front += word[0]
            word = word[1:]

        corrected_word = spell.correction(word)
        if corrected_word != word:
            correction = True

        corrected_text += punctuation_front + corrected_word + punctuation_back + ' '

    if correction:
        return corrected_text[:-1], text
    else:
        return None

def scale(x):
    '''Cross encoder's output ranges from -11 to +11. This scales (arrays of) numbers to be between 0 to 100
    Automatically rescales results as new queries & descriptions come in. I've currently bounded the range to ≈(min - 2σ, max + 2σ) to be safe
    Not sure if this is the best way; maybe environmental variables would be better(?)'''

    with open('scaler.pkl', 'rb') as handle:
        scaler = pickle.load(handle)

    # If all similarity scores are within original range, scale as per usual
    index = (x >= scaler['low']) & (x <= scaler['high'])
    if index.all():
        return (x - scaler['low']) / (scaler['high'] - scaler['low']) * 100

    # If any similarity score exceeds the original range, update pickle file to reflect the new range
    if min(x) < scaler['low']:
        scaler['low'] = max(min(x), -15)
    if max(x) > scaler['high']:
        scaler['high'] = min(max(x), 14)
    with open('scaler.pkl', 'wb') as handle:
        pickle.dump(scaler, handle, protocol = pickle.HIGHEST_PROTOCOL)

    # Then scale data according to new range
    x = (x - scaler['low']) / (scaler['high'] - scaler['low'])
    x[x < scaler['low']] = 0.0
    x[x > scaler['high']] = 1.0
    return x  * 100

def query_models(text, x = 0, n = 5, spellcheck = True):
    '''Takes a user search, returns top n results of cross encoder & 1 randomly selected result of roBERTa
    x is the relevance score threshold (just following the old API)'''

    text = str(text).strip()

    search = text
    if spellcheck:
        temp = autocorrect(text)
        if isinstance(temp, tuple):
            search, _ = temp

    # First query the cross encoder
    cross_sim = crossencoder.predict([(search, i) for _, i in df[['Description']].itertuples()]) # Wall time ≈ 0.4s
    index = np.argsort(-cross_sim)[:n]

    # Then query roBERTa
#     query = biencoder.encode(search, convert_to_tensor = False)
#     query = query.reshape((1, 768))
#     bi_sim = pairwise_distances(emb, query, metric = 'cosine')
#     # Get top 3 similarities, filter those already returned by cross encoder, then randomly pick 1 & append
#     bi_sim = np.argsort(-np.concatenate(bi_sim))[:3]
#     bi_sim = np.random.choice(np.setdiff1d(bi_sim, index))
#     index = np.append(index, bi_sim)

    # Get relevance scores & filter df
    relevance = scale(cross_sim[index])
    output = df.iloc[index, :5]
    output['Relevance'] = relevance
    output = output[output['Relevance'] > x]
    output = output[['Relevance','Scheme','Description', 'Agency', 'Image', 'Link']]

    jsonobject = output.to_json(orient = 'records')
    jsonobject = {  # Prolly wanna include some indicator here for front-end to say something like "Showing results for <search>. Search for <text> instead."
        "data": json.loads(jsonobject)
    }
    return jsonobject
