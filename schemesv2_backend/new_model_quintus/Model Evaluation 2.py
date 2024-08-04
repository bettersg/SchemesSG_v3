import numpy as np
import nltk
import re
import string
import pickle
import pandas as pd
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec
from gensim import corpora, models, similarities
from sentence_transformers import SentenceTransformer, util

# Import schemes
df = pd.read_csv('df.csv')

# Get rid of half-assed descriptions
df = df[df['Description'].str.len() >= 50]

# Sentence Transformers requires index to be correct
df.reset_index(inplace = True, drop = True)

def Cleaner(text):
    '''Input: df(str); Output: df([str, str])'''
    wn = nltk.WordNetLemmatizer()
    stopwords = nltk.corpus.stopwords.words('english') + ['nan']
    punc = string.punctuation.replace('$', '')
    
    # Get rid of weird encoding like non-ASCII characters 
    text = ''.join([i if (i in string.printable) & (i not in punc) else ' ' for i in text.lower()])
    text = re.sub('\n|-|\s+', ' ', text)
    tokens = re.split(' ', text.strip())
    tokens = [wn.lemmatize(i) for i in tokens if i not in stopwords]
    return tokens

# Generate tokens for Doc2Vec & LSI
df['Tokens'] = df['Description'].apply(Cleaner)

# Train LSI model
dic = corpora.Dictionary(df['Tokens'])
corpus = [dic.doc2bow(i) for i in df['Tokens']]
tfidf = models.TfidfModel(corpus, id2word = dic)
corpus = tfidf[corpus]
lsi = models.LsiModel(corpus, id2word = dic, num_topics = 300)

# Train Doc2Vec model
docs = [TaggedDocument(doc, [i]) for i, doc in df[['Description']].itertuples()]
d2v = Doc2Vec(docs, dm = 0, vector_size = 300, window = 10, min_count = 1, epochs = 200, seed = 117)

# Open pre-trained Distilbert feature extraction model
with open('embeddings.pkl', 'rb') as handle:
    emb = pickle.load(handle)
model = SentenceTransformer('sentence-transformers/distilbert-base-nli-mean-tokens')

# Import user queries & clean
queries = pd.read_csv('Queries.csv')
queries = queries[(queries['Query'].notna()) & (queries['Query'].str.contains('test') == False) & (queries['Query'].str.len() > 5)]
queries.drop_duplicates(inplace = True)
queries = queries.sample(150)
queries.reset_index(drop = True, inplace = True)

results = []

for i, _, query, _ in queries.itertuples():
    query = query.strip()
    tokens = nltk.word_tokenize(query)
    
    # Get top 3 indexes for LSI
    vec_bow = dic.doc2bow(tokens)
    vec_lsi = lsi[vec_bow]
    index = similarities.MatrixSimilarity(lsi[corpus])
    sim = sorted(enumerate(index[vec_lsi]), key = lambda i : -i[1])
    lsi_result = np.array(sim)[:3, 0].astype(int)
    
    # Get top 3 indexes for Doc2Vec
    vec = d2v.infer_vector(tokens)
    sim = d2v.docvecs.most_similar([vec], topn = 3)
    d2v_result = np.array(sim)[:, 0].astype(int)
    
    # Get top 3 indexes for Distilbert
    search = model.encode(queries.iloc[i, 1])
    cosine = util.pytorch_cos_sim(search, emb)
    st_result = np.argsort(-np.array(cosine[0]))[:3].astype(int)

    for j in range(3):
        if j == 0:
            results.append([i + 1, query, f'Result {j + 1}', df.iloc[lsi_result[j], 1], df.iloc[d2v_result[j], 1], df.iloc[st_result[j], 1]])
        else:
            results.append([np.nan, np.nan, f'Result {j + 1}', df.iloc[lsi_result[j], 1], df.iloc[d2v_result[j], 1], df.iloc[st_result[j], 1]])

df_results = pd.DataFrame(results, columns = ['#', 'Query', 'Result Ranking', 'LSI', 'D2V', 'ST'])
df_results.to_csv('Query Results.csv', index = False)
