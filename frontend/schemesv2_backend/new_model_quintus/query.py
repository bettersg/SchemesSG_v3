import pickle
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from spellchecker import SpellChecker
# Remove if not using LSI
import nltk
import string
import re
from gensim import corpora, models, similarities

df = pd.read_csv('df.csv')

model = SentenceTransformer('paraphrase-mpnet-base-v2')

with open('emb.pkl', 'rb') as handle:
    emb = pickle.load(handle)
with open('mh_emb.pkl', 'rb') as handle:
    mh_emb = pickle.load(handle)

spell = SpellChecker()
# Add words to vocabulary. Can continue adding as new queries come in, but would advise not to go too far; may inadvertently generate a lot of false positives
add = ['msf', 'sso', 'comcare', 'nkf', 'declutter', 'kikuchi', 'covid', 'covid-19', 'covid19', 'serangoon', 'sengkang', 'hougang', 'sinda', 'bukit', 'panjang', 'ubi',
       'taman', 'jurong', 'yishun', '4d']
spell.word_frequency.load_words(add)

def autocorrect(text):
    '''If text was autocorrected, function returns a tuple. Else, returns None
    Mostly works if only 1 character was wrong. Wall time is 160 - 170ms
    Cannot autocorrect words with punctuation in between (mostly typos in contractions, e.g. "havn't")
    Singaporean/ethnic words/names may be autocorrected into something else; medical terms may be corrected insensitively, e.g. "Kikuchi" into "kimchi"'''
    
    tokens = text.split()
    corrected_text = ''
    correction = False
    
    punctuation = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    
    for _, word in enumerate(tokens):
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
    return (x + 1) * 50

def call_lsi(search):
    '''Calls the LSI model & returns the row index of the top result in df.csv'''
    with open('dic.pkl', 'rb') as handle:
        dic = pickle.load(handle)
    with open('corpus.pkl', 'rb') as handle:
        corpus = pickle.load(handle)
    lsi = models.LsiModel(corpus, id2word = dic, num_topics = 300)
    tokens = nltk.word_tokenize(search.lower())

    # Get top 3 indexes for LSI
    vec_bow = dic.doc2bow(tokens)
    vec_lsi = lsi[vec_bow]
    index = similarities.MatrixSimilarity(lsi[corpus])
    return np.argmax(index[vec_lsi])

def search_similar_schemes(text, relevance = 0, n = 5, spellcheck = True, lsi = True):
    '''Takes a user search, returns top n results. "relevance" is the relevance score threshold (from the old API)'''
    
    # Clean user search
    text = str(text).strip()
    search = text
    if spellcheck:
        temp = autocorrect(text)
        if isinstance(temp, tuple):
            search, _ = temp
    
    # Get vanilla similarity to schemes
    query = model.encode(search)
    sim = util.pytorch_cos_sim(query, emb)
    sim = np.array(sim[0])
    
    # Add a weight for mental health queries
    mh_sim = util.pytorch_cos_sim(query, mh_emb)
    mh_sim = np.array(mh_sim[0]).max()
    
    mh = [
        'abuse', 'bullying', 'bullied', 'depressed', 'depression', 'suicid', 'troubled', 'violen', ' stress', 'mental health', 'distress', 'scared', 'assault', 'trauma',
        'counselling', 'counsellor', 'therapist', 'therapy', 'psychiatri', 'psycholog',
        'autistic', 'autism', 'schizo', 'epilepsy', 'adhd', 'addict', 'dementia', 'alzheimer']
    
    mh_schemes = 'mental health|counselling|emotional care|casework'
    
    if (mh_sim > .7) | (any(substring in search.lower() for substring in mh)):
        mh_index = df['Scheme Type'].str.lower().str.contains(mh_schemes) | df['What it gives'].str.lower().str.contains(mh_schemes)
        # After scaling, relevance score will increase by 10
        sim[mh_index] += .2
    
    index = np.argsort(-sim)[:n]
    
    # Add alternative results from LSI
    if lsi:
        lsi_index = call_lsi(search)
        if (lsi_index not in index) & (scale(sim[lsi_index]) > .5):
            index = np.append(index, lsi_index)
        
    # Get relevance scores & filter df
    sim = scale(sim[index])
    df_out = df.loc[index, ['Scheme', 'Description', 'Agency', 'Image', 'Link']]
    df_out['Relevance'] = sim
    df_out = df_out.loc[df_out['Relevance'] > relevance, ['Relevance', 'Scheme', 'Description', 'Agency', 'Image', 'Link']]
    
    jsonobject = df_out.to_json(orient = 'records')
    # Might wanna include some indicator here for front-end to say something like "Showing results for <search>. Search for <text> instead."
    return {'data' : json.loads(jsonobject)}
