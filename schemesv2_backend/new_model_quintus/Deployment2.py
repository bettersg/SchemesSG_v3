#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pickle
import json
import numpy as np
import pandas as pd
from decouple import config
import requests
from sentence_transformers import util
import re
from string import punctuation
from spellchecker import SpellChecker

df = pd.read_csv('df.csv')
# Until there's proper QC on schemes dataset
df = df[df['Description'].str.len() >= 50]

with open('embeddings.pkl', 'rb') as handle:
    emb = pickle.load(handle)

# Authorize HuggingFace Inference API
api = config('api', default = '')
API_URL = 'https://api-inference.huggingface.co/models/sentence-transformers/distilbert-base-nli-mean-tokens'
headers = {'Authorization': api}

spell = SpellChecker()
# Add words to vocabulary. Can continue adding as new queries come in, but would advise not to go too far; may inadvertently generate a lot of false positives
add = ['msf', 'sso', 'comcare', 'nkf', 'declutter', 'kikuchi', 'covid', 'covid-19', 'covid19', 'serangoon', 'sengkang', 'hougang', 'sinda', 'bukit', 'panjang', 'ubi',
       'taman', 'jurong', 'yishun', '4d']
spell.word_frequency.load_words(add)

def inference(payload):
    '''Sentence Transformer feature extraction'''
    response = requests.post(API_URL, headers = headers, json = payload)
    return response.json()

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
    '''Takes (arrays of) numbers between -1 to 1, scales to be between 0 to 100'''
    return (x + 1) / 2 * 100

def query_models(text, relevance_threshold = 0, n = 10, spellcheck = True):
    '''Takes a user search, returns top n results of distilbert (using feature extraction under HuggingFace's Inference API)
    relevance_threshold just follows the old API'''
    
    text = str(text).strip()
    
    search = text
    if spellcheck:
        temp = autocorrect(text)
        if isinstance(temp, tuple):
            search, _ = temp
    
    # Problem is waiting for the model can take like 20s. Plus HuggingFace's Inference API has crashed on me for hours on end.
    # For 1st problem, I can set up fail-safe models using Doc2Vec or LSI after 5s etc., but I worry that it will always be triggered
    # I can setup fail-safe models using Doc2Vec or LSI, but in the meantime just try it first.
    query = inference({'inputs' : search, 'options' : {'use_cache' : True, 'wait_for_model' : True}})
    cosine = util.pytorch_cos_sim(query, emb)
    sim = np.array(cosine[0])
    sim_index = np.argsort(-sim)[:n]
    
    # Get relevance scores & filter df
    output = df.iloc[sim_index, :5]
    output['Relevance'] = scale(sim)[sim_index]
    output = output[output['Relevance'] > relevance_threshold]
    output = output[['Relevance','Scheme','Description', 'Agency', 'Image', 'Link']]
    
    jsonobject = output.to_json(orient = 'records')
    jsonobject = {  # Prolly wanna include some indicator here for front-end to say something like "Showing results for <search>. Search for <text> instead."
        'data' : json.loads(jsonobject) 
    }
    return jsonobject
