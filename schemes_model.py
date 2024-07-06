#https://radimrehurek.com/gensim/auto_examples/core/run_topics_and_transformations.html

import gensim
import pandas as pd
import spacy
import operator
import re
import string
import json
import codecs

df_schemes = pd.read_csv('df.csv', encoding='cp1252')#Needed to map the scheme names back to 
dictionary = gensim.corpora.Dictionary.load('weights_generation/dictionary') #Needed to construct mappings from BOW of the query term to the dictionary which is already preloaded

schemes_tfidf_model = gensim.models.TfidfModel.load("weights_generation/tfidf.model") #Needed to feed into the LSI model

schemes_lsi_model = gensim.models.LsiModel.load("weights_generation/lsi.model") #Final model
schemes_lsi_corpus = gensim.corpora.MmCorpus('weights_generation/schemes_lsi_model_mm') #Needed to create the matrix similarity index

spacy_nlp = spacy.load('en_core_web_sm')

#For mentalhealth
import pickle
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
nltk.download('punkt')

tvec_optimised = pickle.load(open('weights_generation/tvec', 'rb'))
mhmodel = pickle.load(open('weights_generation/mentalhealth', 'rb'))

#create list of punctuations and stopwords
punctuations = string.punctuation
stop_words = spacy.lang.en.stop_words.STOP_WORDS

to_delete = ["alone","themselves"]
for elem in to_delete:
    stop_words.discard(elem)
stop_words.add("client")

def spacy_tokenizer(sentence):
    #remove distracting single quotes
    sentence = re.sub('\'','',sentence)
    #replace extra spaces with single space
    sentence = re.sub(' +',' ',sentence)
    #remove unwanted lines starting from special charcters
    sentence = re.sub(r'\n: \'\'.*','',sentence)
    sentence = re.sub(r'\n!.*','',sentence)
    sentence = re.sub(r'^:\'\'.*','',sentence)
    #remove non-breaking new line characters
    sentence = re.sub(r'\n',' ',sentence)
    #remove punctuations
    sentence = re.sub(r'[^\w\s]',' ',sentence)
    #creating token object
    tokens = spacy_nlp(sentence)
    #lower, strip and lemmatize
    tokens = [word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in tokens]
    #remove stopwords, and exclude words less than 2 characters
    tokens = [word for word in tokens if word not in stop_words and word not in punctuations and len(word) > 2]
    #return tokens
    return tokens

#create stemmer for mentalhealth
porter = PorterStemmer()
def stemSentence(sentence):
    token_words=word_tokenize(sentence)
    token_words
    stem_sentence=[]
    for word in token_words:
        stem_sentence.append(porter.stem(word))
        stem_sentence.append(" ")
    return "".join(stem_sentence)

from gensim.similarities import MatrixSimilarity
schemes_index = MatrixSimilarity(schemes_lsi_corpus, num_features = schemes_lsi_corpus.num_terms)

#Search similarity
from operator import itemgetter
counter = 0
def search_similar_schemes(search_term, x):
    global counter
    query_bow = dictionary.doc2bow(spacy_tokenizer(search_term))
    query_tfidf = schemes_tfidf_model[query_bow]
    query_lsi = schemes_lsi_model[query_tfidf]
    schemes_index.num_best = 50
    schemes_list = schemes_index[query_lsi]
    schemes_list.sort(key=itemgetter(1), reverse=True)
    schemes_names = []
    for j, scheme in enumerate(schemes_list):
        schemes_names.append (
            {
                'Relevance': round((scheme[1] * 100),2),
                'Scheme': df_schemes['Scheme'][scheme[0]],
                'Description': df_schemes['Description'][scheme[0]],
                'Agency': df_schemes['Agency'][scheme[0]],
                'Image': df_schemes['Image'][scheme[0]],
                'Link': df_schemes['Link'][scheme[0]],
                'What it gives': df_schemes['What it gives'][scheme[0]],
                'Scheme Type': df_schemes['Scheme Type'][scheme[0]]
            }
        )
        if j == (schemes_index.num_best-1):
            break
  
    output = pd.DataFrame(schemes_names, columns=['Relevance','Scheme','Description', 'Agency', 'Image', 'Link', 'What it gives', 'Scheme Type'])

    mhprob = mhmodel.predict_proba(tvec_optimised.transform([str(stemSentence(search_term))]).todense())[0][1]

    output['Relevance'] = output.apply(lambda y: (y['Relevance'] * 1.05 ) if ((('mental health' or 'counselling' or 'emotional care' or 'casework' in y['Scheme Type'].lower()) or
                                                                              ('mental health' or 'counselling' or 'emotional care' or 'casework' in y['What it gives'].lower())) and 
                                                                              (mhprob > 0.55)) else y['Relevance'], axis=1)
    output = output.sort_values(by=['Relevance'], ascending= False)
    output = output[output['Relevance']>x]
    jsonobject = output.to_json(orient = "records") #.encode('unicode-escape').decode('unicode-escape')
    counter = counter + 1
    jsonobject = {
        "data": json.loads(jsonobject),
        "mh": mhprob
    }
    return jsonobject