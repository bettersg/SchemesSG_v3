import spacy
import re

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

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
    return [preprocessing(x) for x in all_needs]

# Helper function to split the query into sentences
def split_into_sentences(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents]
