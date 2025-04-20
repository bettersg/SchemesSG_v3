import os
import csv
import argparse  # Import argparse
import sys  # Import sys for logger output
from urllib.parse import urljoin, urlparse # Import urljoin and urlparse for handling relative URLs
import io # Import io for handling byte streams
import string # Import string for text validation

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.api_core import exceptions as google_exceptions  # Import google exceptions
import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger # Import loguru
# Add imports for retry mechanism
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import ConnectionError # Import ConnectionError specifically
import time # Import time for potential delays if needed
from pypdf import PdfReader # Import PdfReader

# Set up argument parser
parser = argparse.ArgumentParser(description='Scrape website text and update Firestore.')
parser.add_argument('creds_file', help='Path to the Firebase credentials file.')
args = parser.parse_args()

# Initialize Logger
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    colorize=True,
    backtrace=True,
)
logger.info("Logger initialised")

# Use a service account to connect to firestore.
cred = credentials.Certificate(args.creds_file) # Use the path from arguments

app = firebase_admin.initialize_app(cred)

db = firestore.client()

# Configure Retry Strategy
retry_strategy = Retry(
    total=3,  # Total number of retries
    backoff_factor=1, # Wait 1s, 2s, 4s between retries
    status_forcelist=[429, 500, 502, 503, 504, 520], # Retry on these status codes
    allowed_methods=["HEAD", "GET", "OPTIONS"], # Retry only on idempotent methods
    respect_retry_after_header=True
)

# Create a Session with the Retry strategy
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

# More comprehensive headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1', # Do Not Track Request Header
    'Upgrade-Insecure-Requests': '1'
}

# Define the CSV file path
error_log_file = "dataset_worfklow/Main_scrape/error_log.csv"
# Function to initialize the CSV file (always overwrite)
def initialize_csv(file_path):
    # Ensure the directory exists before trying to open the file
    directory = os.path.dirname(file_path)
    if directory: # Ensure directory is not an empty string (if file is in root)
        os.makedirs(directory, exist_ok=True)

    # Open in 'w' mode to overwrite/create the file and write the header
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["doc_id", "link", "error"])  # Write the header
    logger.info(f"Error log CSV initialized at: {file_path}")

# Function to log errors to the CSV file
def log_error_to_csv(doc_id, link, error_message):
    # Ensure error_message is a string
    error_message_str = str(error_message)
    # Also log the error using the main logger
    logger.error(f"Logging error for doc_id '{doc_id}' (Link: {link}): {error_message_str}")
    with open(error_log_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([doc_id, link, error_message_str])

# Initialize the CSV file (this will now reset it)
initialize_csv(error_log_file)

# Function to find logo URL
def find_logo_url(soup, base_url):
    logger.debug(f"Attempting to find logo for: {base_url}")
    possible_logos = []

    # 1. Open Graph image
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        possible_logos.append(urljoin(base_url, og_image["content"]))
        logger.debug(f"Found og:image: {possible_logos[-1]}")

    # 2. Favicons/Apple Touch Icons (prefer higher resolution if possible)
    icon_rels = ["apple-touch-icon", "icon", "shortcut icon"]
    for rel in icon_rels:
        link_tag = soup.find("link", rel=rel)
        if link_tag and link_tag.get("href"):
            logo_url = urljoin(base_url, link_tag["href"])
            possible_logos.append(logo_url)
            logger.debug(f"Found link rel='{rel}': {logo_url}")

    # 3. Image tags (look for 'logo'/'brand' in src or alt, prioritize header)
    header = soup.find("header")
    search_area = header if header else soup # Search header first, then whole soup

    for img in search_area.find_all("img"):
        src = img.get("src", "").lower()
        alt = img.get("alt", "").lower()
        # Basic check for 'logo' or 'brand' in src or alt
        if "logo" in src or "brand" in src or "logo" in alt or "brand" in alt:
            img_url = urljoin(base_url, img["src"]) # Use original src for urljoin
            # Avoid tiny images if size is specified and obvious (heuristic)
            width = img.get("width")
            height = img.get("height")
            try:
                if width and int(width) < 32: continue
                if height and int(height) < 32: continue
            except ValueError:
                pass # Ignore if width/height are not integers

            possible_logos.append(img_url)
            logger.debug(f"Found img tag with logo hint: {img_url}")

    # Prioritize logo candidates (simple heuristic: prefer OG, then icons, then imgs)
    # Remove duplicates while preserving order (simple list conversion)
    seen = set()
    unique_logos = []
    for logo in possible_logos:
        if logo not in seen:
            seen.add(logo)
            unique_logos.append(logo)

    if unique_logos:
        logger.info(f"Found potential logo for {base_url}: {unique_logos[0]}")
        return unique_logos[0] # Return the first unique logo found (based on priority)
    else:
        logger.warning(f"Could not find a logo for: {base_url}")
        return None

# Function to validate if the text looks like readable text
def is_valid_text(text, bad_char_threshold=0.2):
    """Checks if the proportion of non-printable Unicode characters (excluding common whitespace)
    in the text is below a threshold."""
    if not text or not isinstance(text, str):
        return False # Handle None or non-string input

    total_len = len(text)
    if total_len == 0:
        return True # Empty string is considered valid

    allowed_whitespace = {'\n', '\r', '\t'}
    non_printable_count = 0

    for char in text:
        # Check if the character is NOT printable AND not allowed whitespace
        if not char.isprintable() and char not in allowed_whitespace:
            non_printable_count += 1

    try:
        ratio = non_printable_count / total_len
        # Return True if the ratio of bad characters is BELOW the threshold
        is_valid = ratio < bad_char_threshold
        if not is_valid:
            logger.trace(f"Text validation failed: Ratio of non-printable chars ({ratio:.2f}) >= threshold ({bad_char_threshold})")
        return is_valid
    except ZeroDivisionError: # Should be caught by the initial total_len check, but just in case
        return True

# Function to scrape text and get soup object from a URL
def scrape_content(link):
    mod_security_error_signature = "Not Acceptable!An appropriate representation of the requested resource could not be found on this server. This error was generated by Mod_Security."
    try:
        # Perform a HEAD request first to check content type without downloading full body
        head_response = session.head(link, verify=False, timeout=15, headers=HEADERS, allow_redirects=True)
        head_response.raise_for_status()
        content_type = head_response.headers.get('Content-Type', '').lower()
        is_pdf = content_type.startswith('application/pdf') or link.lower().endswith('.pdf')

        # Now perform GET request to fetch content
        response = session.get(link, verify=False, timeout=30, headers=HEADERS)
        response.raise_for_status()

        if is_pdf:
            logger.info(f"Processing PDF link: {link}")
            try:
                # Read PDF from memory
                pdf_file = io.BytesIO(response.content)
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n" # Add newline between pages
                logger.info(f"Successfully extracted text from PDF: {link} (Length: {len(text)})")
                return text.strip(), None # Return text, soup is None for PDF
            except Exception as pdf_err:
                logger.error(f"Error processing PDF {link}: {pdf_err}")
                return f"PDF Processing Error: {pdf_err}", None
        else:
            # Handle HTML content
            encoding = response.encoding if 'charset' in response.headers.get('content-type', '').lower() else None
            try:
                soup = BeautifulSoup(response.content, 'lxml', from_encoding=encoding)
            except Exception: # Catch potential issue if lxml is not available
                 soup = BeautifulSoup(response.content, 'html.parser', from_encoding=encoding)

            # Enhanced text extraction (consider removing script/style, keeping structure)
            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                element.decompose() # Remove these tags and their content
            text = soup.get_text(separator='\n', strip=True) # Use newline separator, strip whitespace

            if mod_security_error_signature in text:
                logger.warning(f"Blocked by Mod_Security: {link}")
                return "Blocked by Mod_Security", soup # Return error and soup

            logger.info(f"Successfully scraped HTML: {link} (Length: {len(text)})")
            return text, soup # Return both text and soup object

    except requests.exceptions.HTTPError as e:
        # Check for 404 specifically
        if e.response.status_code == 404:
             logger.warning(f"HTTP 404 Not Found for URL '{link}'.")
             return "HTTP Error: 404", None
        logger.error(f"HTTP Error scraping URL '{link}' after retries: {e}")
        return f"HTTP Error: {e.response.status_code}", None
    # Catch ConnectionError specifically
    except ConnectionError as e:
        logger.error(f"Connection Error scraping URL '{link}' after retries: {e}")
        return f"Connection Error: {e}", None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error scraping URL '{link}' after retries: {e}")
        return f"Request Error: {e}", None
    except Exception as e:
        logger.error(f"Unexpected scraping error for URL '{link}': {e}")
        return f"Unexpected Scraping Error: {e}", None

# Get all documents from the collection
try:
    logger.info("Starting to stream documents from 'schemes' collection.")
    docs_stream = db.collection("schemes").stream()

    # Set the flag to control scraping behavior (No longer used for skipping, but kept for potential future use)
    skip_if_scraped = True # Consider making this an argument if needed frequently

    for doc in docs_stream:
        doc_ref = db.collection("schemes").document(doc.id)
        doc_data = None # Initialize doc_data

        try:
            # Convert the document to a dictionary to check for fields
            doc_data = doc.to_dict()
            if doc_data is None:
                raise ValueError("Document data is None, cannot process.")

            # Ensure 'scraped_text' field exists, initialize if not
            if "scraped_text" not in doc_data:
                try:
                    doc_ref.update({"scraped_text": ""})
                    logger.info(f"Initialized 'scraped_text' field for document {doc.id}.")
                    doc_data["scraped_text"] = "" # Update local dict as well
                except Exception as e_init:
                    error_message = f"Error initializing 'scraped_text': {e_init}"
                    logger.error(f"{error_message} for document {doc.id}") # Covered by log_error_to_csv
                    log_error_to_csv(doc.id, doc_data.get("link", "N/A"), error_message)
                    continue # Skip to the next document if initialization fails

            # Check if scraping should be skipped based on 'scraped_text' field
            should_skip_scraping = skip_if_scraped and doc_data.get("scraped_text")

            # Check if image field is already populated
            image_already_populated = doc_data.get("image")

            # Skip if both text is scraped AND image is populated (and skip_if_scraped is True)
            if should_skip_scraping and image_already_populated:
                logger.info(f"Skipping doc {doc.id}: 'scraped_text' exists and 'image' is populated.")
                continue
            elif should_skip_scraping:
                logger.info(f"Skipping text scraping for doc {doc.id} ('scraped_text' exists), but will check for logo.")
                # Allow proceeding to potentially find the logo even if text exists
            elif image_already_populated:
                 logger.info(f"Image already populated for doc {doc.id}, will only scrape text if needed.")
                 # Allow proceeding to scrape text if needed

            url_to_scrape = doc_data.get("link")
            if url_to_scrape:
                logger.debug(f"Attempting to scrape content for doc {doc.id}: {url_to_scrape}")
                # Scrape content only if not skipping text scraping OR if image isn't populated yet
                scraped_content = None
                soup = None
                is_error = False
                error_message_scrape = None # Separate var for scraping error message

                if not should_skip_scraping or not image_already_populated:
                    scraped_content, soup = scrape_content(url_to_scrape)

                    # Validate scraped content
                    if isinstance(scraped_content, str) and not scraped_content.startswith("HTTP Error:") and not scraped_content.startswith("Connection Error:") and not scraped_content.startswith("Request Error:") and not scraped_content.startswith("Unexpected Scraping Error:") and not scraped_content.startswith("PDF Processing Error:") and not scraped_content == "Blocked by Mod_Security":
                        if not is_valid_text(scraped_content):
                            logger.warning(f"Scraped content for {doc.id} ({url_to_scrape}) failed validation (likely binary or garbled). Storing empty string.")
                            # Log the failure but store empty string instead of bad data
                            log_error_to_csv(doc.id, url_to_scrape, "Text validation failed (binary/garbled)")
                            scraped_content = "" # Set to empty string to avoid storing bad data
                        else:
                            logger.info(f"Text validation passed for {doc.id}.")
                    else:
                        # If scrape_content returned an error message, log it and ensure content is marked as error
                        is_error = True
                        error_message_scrape = scraped_content if isinstance(scraped_content, str) else "Unknown scraping error"
                        log_error_to_csv(doc.id, url_to_scrape, error_message_scrape)
                        scraped_content = "" # Ensure we store empty string on error

                if is_error:
                    # Log the scraping error
                    logger.error(f"Scraping error for document {doc.id} ({url_to_scrape}): {error_message_scrape}")
                    log_error_to_csv(doc.id, url_to_scrape, error_message_scrape)
                    # Update Firestore with the error status (optional, but can be useful)
                    try:
                        doc_ref.update({"scraped_text": f"ERROR: {error_message_scrape}"})
                        logger.info(f"Updated document {doc.id} with scraping error status.")
                    except Exception as e_update_err:
                         logger.error(f"Failed to update document {doc.id} with error status: {e_update_err}")
                         # Log this secondary error to CSV as well
                         log_error_to_csv(doc.id, url_to_scrape, f"Failed to update doc with primary error: {e_update_err}")

                    # Do not attempt logo finding if scraping failed
                else:
                    update_data = {}
                    logo_url = None

                    # Find and update logo only if image isn't populated OR if we got a valid soup object
                    # (We might have skipped text scraping but still need the logo)
                    if not image_already_populated:
                        logo_url = None
                        if soup: # We need soup to find the logo
                             logo_url = find_logo_url(soup, url_to_scrape)
                        elif not should_skip_scraping and not is_error:
                            # If we didn't scrape text but should have (e.g., PDF), log it
                             logger.warning(f"Cannot find logo for {doc.id} as no HTML soup object was generated (URL: {url_to_scrape}).")
                        elif should_skip_scraping:
                             # If we skipped text scraping, we need to fetch soup specifically for the logo
                             logger.info(f"Text scraping was skipped for {doc.id}, fetching page again to find logo.")
                             _, temp_soup = scrape_content(url_to_scrape) # Ignore text result here
                             if temp_soup:
                                 logo_url = find_logo_url(temp_soup, url_to_scrape)
                             else:
                                 logger.warning(f"Could not fetch page or find soup to get logo for {doc.id} after text skip.")

                        if logo_url:
                            logger.info(f"Preparing to update 'image' for doc {doc.id} with logo: {logo_url}")
                            update_data["image"] = logo_url
                        elif not is_error: # Don't log missing logo if there was a scrape error anyway
                             # Log only if logo finding failed and we expected to find one
                            log_error_to_csv(doc.id, url_to_scrape, "Logo not found")

                    # Update scraped_text only if it wasn't skipped and no error occurred during scraping
                    if not should_skip_scraping and not is_error and scraped_content is not None:
                         logger.info(f"Preparing to update 'scraped_text' for doc {doc.id} (Length: {len(scraped_content)})")
                         update_data["scraped_text"] = scraped_content

                    # Update Firestore only if there's something to update
                    if update_data:
                        try:
                            doc_ref.update(update_data)
                            log_parts = []
                            if "scraped_text" in update_data: log_parts.append("scraped text")
                            if "image" in update_data: log_parts.append("found logo")
                            logger.success(f"Successfully updated document {doc.id} ({', '.join(log_parts)}).")
                        except Exception as e_update:
                            error_message = f"Error updating document {doc.id} after processing: {e_update}"
                            logger.error(error_message)
                            log_error_to_csv(doc.id, url_to_scrape, error_message)
                    elif not should_skip_scraping and scraped_content is None:
                         # Handle case where scrape function might return None unexpectedly and wasn't skipped
                         error_message = f"Scraping returned None unexpectedly for document {doc.id} ({url_to_scrape})"
                         logger.warning(error_message)
                         log_error_to_csv(doc.id, url_to_scrape, error_message)
                    elif not update_data:
                         logger.info(f"No update needed for document {doc.id} (already scraped/populated or no logo found).")

            else:
                error_message = f"Document {doc.id} does not have a 'link' field."
                logger.warning(error_message) # Covered by log_error_to_csv
                log_error_to_csv(doc.id, "N/A", error_message)

        except Exception as e_doc:
            # Catch errors during processing of a single document (reading, updating, etc.)
            error_message = f"Error processing document {doc.id}: {e_doc}"
            logger.exception(error_message) # Use logger.exception to include traceback, covered by log_error_to_csv
            link = doc_data.get("link", "N/A") if doc_data else "N/A"
            log_error_to_csv(doc.id, link, error_message)
            continue # Continue to the next document

except google_exceptions.DeadlineExceeded as e_deadline:
    error_message = f"Firestore deadline exceeded during stream iteration: {e_deadline}"
    logger.critical(error_message) # Covered by log_error_to_csv
    log_error_to_csv("N/A", "N/A", error_message)
    logger.critical("Stopping script due to Firestore DeadlineExceeded error.")
except Exception as e_main:
    # Catch any other unexpected errors in the main script execution
    error_message = f"An unexpected error occurred in the main script: {e_main}"
    logger.critical(error_message, exc_info=True) # Use critical and include traceback, covered by log_error_to_csv
    log_error_to_csv("N/A", "N/A", error_message)
    logger.critical("Stopping script due to an unexpected main error.", exc_info=True)

logger.info("Script finished.")
