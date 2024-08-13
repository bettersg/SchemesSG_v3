import re

def clean_text(text):
    sentence = re.sub('\'', '', text)  # Remove distracting single quotes
    sentence = re.sub(' +', ' ', sentence)  # Replace extra spaces
    sentence = re.sub(r'\n: \'\'.*', '', sentence)  # Remove specific unwanted lines
    sentence = re.sub(r'\n!.*', '', sentence)
    sentence = re.sub(r'^:\'\'.*', '', sentence)
    sentence = re.sub(r'\n', ' ', sentence)  # Replace non-breaking new lines with space
    sentence = re.sub('[^A-Za-z0-9 ]+', '', sentence)
    return sentence

def clean_scraped_text(text):
    sentence = re.sub('\'', '', text)  # Remove distracting single quotes
    sentence = re.sub(' +', ' ', sentence)  # Replace extra spaces
    sentence = re.sub(r'\n: \'\'.*', '', sentence)  # Remove specific unwanted lines
    sentence = re.sub(r'\n!.*', '', sentence)
    sentence = re.sub(r'^:\'\'.*', '', sentence)
    sentence = re.sub(r'\n', ' ', sentence)  # Replace non-breaking new lines with space
    sentence = re.sub('[^A-Za-z0-9 @]+', '', sentence)
    return sentence
