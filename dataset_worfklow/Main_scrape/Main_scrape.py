import os
import csv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Use a service account to connect to firestore.
cred = credentials.Certificate("../schemessg-v3-dev-firebase-adminsdk-fehbb-e554498306.json")

app = firebase_admin.initialize_app(cred)

db = firestore.client()

# Define the CSV file path
error_log_file = "error_log.csv"
# Function to initialize the CSV file if it doesn't exist
def initialize_csv(file_path):
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["doc_id", "link", "error"])  # Write the header
# Function to log errors to the CSV file
def log_error_to_csv(doc_id, link, error_message):
    with open(error_log_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([doc_id, link, error_message])

# Initialize the CSV file
initialize_csv(error_log_file)


##def hello_pubsub(event, context):
    ##"""Triggered from a message on a Cloud Pub/Sub topic.

    ##Args:
     ##   event (dict): Event payload.
     ##   context (google.cloud.functions.Context): Metadata for the event.  

    ##"""

# Function to scrape text from a URL
def scrape_text_from_url(link):
    try:
        response = requests.get(link, verify=False)
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
docs = db.collection("schemes").stream()

# Set the flag to control scraping behavior
skip_if_scraped = True  # Change to False if you want to always scrape and update


for doc in docs:
    doc_ref = db.collection("schemes").document(doc.id)

    # Convert the document to a dictionary to check for fields
    doc_data = doc.to_dict()
    if "scraped_text" not in doc_data:
        try:
            # Initialize the field with an empty string
            doc_ref.update({"scraped_text": ""})
            print(f"Initialized 'scraped_text' field for document {doc.id}.")
        except Exception as e:
            error_message = str(e)
            print(f"Error initializing 'scraped_text' field for document {doc.id}: {error_message}")
            log_error_to_csv(doc.id, None, error_message)
            continue  # Skip to the next document if initialization fails

    # Skip scraping if the 'scraped_text' field already has a value and skip_if_scraped is True
    if skip_if_scraped and doc_data.get("scraped_text"):
        print(f"Skipping scraping for document {doc.id} as 'scraped_text' already has a value.")
        continue

    # Assuming you have a field "URL" in your documents that points to the page to scrape
    url_to_scrape = doc.to_dict().get("Link")
    if url_to_scrape:
        try:
            scraped_text = scrape_text_from_url(url_to_scrape)
            doc_ref.update({"scraped_text": scraped_text})
            print(f"Updated document {doc.id} with scraped text.")
        except Exception as e:
            error_message = str(e)
            print(f"Error scraping or updating document {doc.id}: {error_message}")
            # Log the error to CSV
            log_error_to_csv(doc.id, url_to_scrape, error_message)
    else:
        error_message = f"Document {doc.id} does not have a Link field."
        print(error_message)
        log_error_to_csv(doc.id, url_to_scrape, error_message)
