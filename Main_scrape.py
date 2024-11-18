import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Use a service account to connect to firestore.
cred = credentials.Certificate("firebase credential key")

app = firebase_admin.initialize_app(cred)

db = firestore.client()

##def hello_pubsub(event, context):
    ##"""Triggered from a message on a Cloud Pub/Sub topic.

    ##Args:
     ##   event (dict): Event payload.
     ##   context (google.cloud.functions.Context): Metadata for the event.   

    ##"""

# Function to scrape text from a URL
def scrape_text_from_url(link):
    try:
        response = requests.get(link)
        # Determine the encoding of the response
        encoding = response.encoding if 'charset' in response.headers.get('content-type', '').lower() else None
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding=encoding)
        # Extract text from the webpage and strip whitespaces
        text = soup.get_text(strip=True)
        return text
    except requests.RequestException as e:
        print(f"Error scraping URL '{link}': {e}")
        return "Link does not work"

# Get all documents from the collection
docs = db.collection("schemeEntries").stream()  

for doc in docs:
    doc_ref = db.collection("schemeEntries").document(doc.id)

    # Assuming you have a field "URL" in your documents that points to the page to scrape
    url_to_scrape = doc.to_dict().get("Link")
    if url_to_scrape:
        try:
            scraped_text = scrape_text_from_url(url_to_scrape)
            doc_ref.update({"scraped_text": scraped_text})
            print(f"Updated document {doc.id} with scraped text.")
        except Exception as e:
            print(f"Error scraping or updating document {doc.id}: {e}")
    else:
        print(f"Document {doc.id} does not have a Link field.")

