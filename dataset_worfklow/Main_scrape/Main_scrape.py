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
    'Accept-Encoding': 'gzip, deflate, br',  # Explicitly accept Brotli compression
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

    # 2. Twitter Card image
    twitter_image = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter_image and twitter_image.get("content"):
        possible_logos.append(urljoin(base_url, twitter_image["content"]))
        logger.debug(f"Found twitter:image: {possible_logos[-1]}")

    # 3. Favicons/Apple Touch Icons (prefer higher resolution if possible)
    icon_rels = ["apple-touch-icon", "icon", "shortcut icon"]
    for rel in icon_rels:
        link_tag = soup.find("link", rel=rel)
        if link_tag and link_tag.get("href"):
            logo_url = urljoin(base_url, link_tag["href"])
            possible_logos.append(logo_url)
            logger.debug(f"Found link rel='{rel}': {logo_url}")

    # 4. Enhanced image tag search with better logo detection
    # Look for images in header, navigation, or with logo-related attributes
    logo_selectors = [
        '.logo', '.brand', '.header-logo', '.site-logo',
        'header img', '.header img', 'nav img', '.navigation img',
        '[class*="logo"]', '[id*="logo"]', '[alt*="logo"]',
        '[alt*="brand"]', '[alt*="company"]'
    ]

    for selector in logo_selectors:
        for img in soup.select(selector):
            src = img.get("src", "")
            if src:
                img_url = urljoin(base_url, src)
                # Avoid data URLs and very small images
                if not img_url.startswith('data:') and not is_tiny_image(img):
                    possible_logos.append(img_url)
                    logger.debug(f"Found logo via selector '{selector}': {img_url}")

    # 5. Fallback: Search for images with logo-related text in alt or title
    for img in soup.find_all("img"):
        src = img.get("src", "").lower()
        alt = img.get("alt", "").lower()
        title = img.get("title", "").lower()

        # Check for logo indicators in various attributes
        logo_indicators = ["logo", "brand", "company", "organization"]
        has_logo_indicator = any(indicator in alt or indicator in title or indicator in src for indicator in logo_indicators)

        if has_logo_indicator and src and not src.startswith('data:'):
            img_url = urljoin(base_url, img["src"])
            if not is_tiny_image(img):
                possible_logos.append(img_url)
                logger.debug(f"Found logo via text analysis: {img_url}")

    # 6. Look for images in header area specifically
    header = soup.find("header")
    if header:
        for img in header.find_all("img"):
            src = img.get("src", "")
            if src and not src.startswith('data:') and not is_tiny_image(img):
                img_url = urljoin(base_url, src)
                possible_logos.append(img_url)
                logger.debug(f"Found logo in header: {img_url}")

    # Prioritize logo candidates and remove duplicates
    seen = set()
    unique_logos = []
    for logo in possible_logos:
        if logo not in seen:
            seen.add(logo)
            unique_logos.append(logo)

    if unique_logos:
        # Prioritize: prefer OG images, then larger images, then others
        best_logo = select_best_logo(unique_logos, soup, base_url)
        logger.info(f"Found potential logo for {base_url}: {best_logo}")
        return best_logo
    else:
        logger.warning(f"Could not find a logo for: {base_url}")
        return None

def is_tiny_image(img):
    """Check if image is likely too small to be a logo"""
    width = img.get("width")
    height = img.get("height")

    try:
        if width and int(width) < 32:
            return True
        if height and int(height) < 32:
            return True
    except (ValueError, TypeError):
        pass

    # Check CSS classes that might indicate small decorative images
    classes = img.get("class", [])
    small_image_indicators = ["icon", "favicon", "small", "tiny", "thumb"]
    if any(indicator in " ".join(classes).lower() for indicator in small_image_indicators):
        return True

    return False

def select_best_logo(logos, soup, base_url):
    """Select the best logo from a list of candidates"""
    if not logos:
        return None

    # If only one logo, return it
    if len(logos) == 1:
        return logos[0]

    # Prioritize logos based on various factors
    scored_logos = []

    for logo in logos:
        score = 0

        # Prefer OG images (highest priority)
        if any(meta.get("content") == logo for meta in soup.find_all("meta", property="og:image")):
            score += 100

        # Prefer larger images
        if "logo" in logo.lower() or "brand" in logo.lower():
            score += 50

        # Prefer images from the same domain
        if urlparse(logo).netloc == urlparse(base_url).netloc:
            score += 25

        # Prefer common logo file patterns
        if any(pattern in logo.lower() for pattern in ["logo", "brand", "header"]):
            score += 20

        # Prefer common image formats
        if logo.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
            score += 10

        scored_logos.append((score, logo))

    # Sort by score (highest first) and return the best
    scored_logos.sort(reverse=True)
    return scored_logos[0][1]

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

        # Ensure content is properly decompressed
        if response.headers.get('content-encoding'):
            logger.info(f"Response is compressed with: {response.headers.get('content-encoding')}")
            # Force decompression by accessing response.content
            try:
                # This should trigger automatic decompression
                content = response.content
                logger.info(f"Decompressed content length: {len(content)} bytes")
            except Exception as e:
                logger.error(f"Failed to decompress content: {e}")
                return f"Decompression Error: {e}", None
        else:
            logger.info("Response is not compressed")

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
            # Handle HTML content with aggressive encoding detection
            logger.info(f"Processing HTML content for: {link}")

            # Debug: Let's see what we're actually getting
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Content-Type header: {response.headers.get('content-type', 'Not set')}")
            logger.info(f"Content length: {len(response.content)} bytes")

            # Check if response content looks valid
            if not check_response_content(response):
                logger.error("Response content appears to be invalid or contains errors")
                return f"Invalid Response: Content appears to be invalid or contains errors", None

            # Show first 200 characters of raw content for debugging
            raw_preview = response.content[:200]
            logger.info(f"Raw content preview: {raw_preview}")

            # Also show a text preview if possible
            try:
                text_preview = response.content.decode('utf-8', errors='ignore')[:500]
                logger.info(f"Text preview: {text_preview}")
            except Exception as e:
                logger.warning(f"Could not create text preview: {e}")

            # Try multiple encoding strategies
            decoded_content = None
            soup = None
            encoding_used = None

            # Strategy 1: Try with requests' apparent encoding
            try:
                response.encoding = response.apparent_encoding
                decoded_content = response.text
                encoding_used = response.apparent_encoding
                logger.info(f"Strategy 1: Using requests.apparent_encoding: {encoding_used}")

                # Test if this gives us readable text
                if is_readable_text(decoded_content):
                    soup = BeautifulSoup(decoded_content, 'lxml')
                    logger.info("Strategy 1 successful - text appears readable")
                else:
                    logger.warning("Strategy 1 failed - text not readable")
                    # Show a preview of what we got
                    preview = decoded_content[:200] if decoded_content else "None"
                    logger.warning(f"Strategy 1 preview: {preview}")
                    decoded_content = None
            except Exception as e:
                logger.warning(f"Strategy 1 failed: {e}")

            # Strategy 2: Try common encodings
            if not decoded_content:
                common_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252', 'cp1252']
                for encoding in common_encodings:
                    try:
                        decoded_content = response.content.decode(encoding, errors='replace')
                        encoding_used = encoding
                        logger.info(f"Strategy 2: Trying {encoding}")

                        if is_readable_text(decoded_content):
                            soup = BeautifulSoup(decoded_content, 'lxml')
                            logger.info(f"Strategy 2 successful with {encoding}")
                            break
                        else:
                            logger.warning(f"Strategy 2 failed with {encoding} - text not readable")
                            # Show a preview of what we got
                            preview = decoded_content[:200] if decoded_content else "None"
                            logger.warning(f"Strategy 2 preview with {encoding}: {preview}")
                            decoded_content = None
                    except Exception as e:
                        logger.warning(f"Strategy 2 failed with {encoding}: {e}")
                        continue

            # Strategy 3: Use chardet with multiple attempts
            if not decoded_content:
                try:
                    import chardet
                    # Try with different confidence levels
                    for confidence_threshold in [0.8, 0.7, 0.6, 0.5]:
                        detected = chardet.detect(response.content)
                        if detected and detected['confidence'] > confidence_threshold:
                            encoding = detected['encoding']
                            logger.info(f"Strategy 3: chardet detected {encoding} with confidence {detected['confidence']:.2f}")

                            try:
                                decoded_content = response.content.decode(encoding, errors='replace')
                                encoding_used = encoding

                                if is_readable_text(decoded_content):
                                    soup = BeautifulSoup(decoded_content, 'lxml')
                                    logger.info(f"Strategy 3 successful with {encoding}")
                                    break
                                else:
                                    logger.warning(f"Strategy 3 failed with {encoding} - text not readable")
                                    # Show a preview of what we got
                                    preview = decoded_content[:200] if decoded_content else "None"
                                    logger.warning(f"Strategy 3 preview with {encoding}: {preview}")
                                    decoded_content = None
                            except Exception as e:
                                logger.warning(f"Strategy 3 failed to decode with {encoding}: {e}")
                                continue
                except ImportError:
                    logger.warning("chardet not available for Strategy 3")
                except Exception as e:
                    logger.warning(f"Strategy 3 failed: {e}")

            # Strategy 4: Last resort - force UTF-8 with error handling
            if not decoded_content:
                logger.warning("All strategies failed, using forced UTF-8 with error handling")
                try:
                    decoded_content = response.content.decode('utf-8', errors='replace')
                    encoding_used = 'utf-8-forced'
                    soup = BeautifulSoup(decoded_content, 'lxml')
                    logger.info("Strategy 4 completed (forced UTF-8)")

                    # Show what we got even if it's not readable
                    preview = decoded_content[:200] if decoded_content else "None"
                    logger.info(f"Strategy 4 preview: {preview}")

                except Exception as e:
                    logger.error(f"Strategy 4 failed: {e}")
                    return f"Encoding Error: Could not decode content with any method", None

            # If we still don't have readable content, try to clean it
            if decoded_content and not is_readable_text(decoded_content):
                logger.warning("Content still not readable after decoding, attempting aggressive cleaning")
                decoded_content = aggressive_text_cleaning(decoded_content)

                if not is_readable_text(decoded_content):
                    logger.error("Content still not readable after aggressive cleaning")
                    # Show what we have after cleaning
                    preview = decoded_content[:200] if decoded_content else "None"
                    logger.error(f"After cleaning preview: {preview}")
                    return f"Encoding Error: Content remains unreadable after all attempts", None

            logger.info(f"Successfully decoded content using {encoding_used}")

            # Enhanced text extraction with better content filtering
            # Remove unwanted elements that don't contribute to main content
            unwanted_selectors = [
                'script', 'style', 'nav', 'aside', 'footer',
                '.header', '.navigation', '.sidebar', '.footer',
                '.menu', '.breadcrumb', '.pagination',
                '.social-share', '.related-posts', '.comments',
                '.advertisement', '.ads', '.banner',
                '.cookie-notice', '.popup', '.modal',
                '.newsletter-signup', '.subscribe',
                '.search-form', '.search-results'
            ]

            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()

            # Remove common navigation and utility elements
            for element in soup(['header', 'footer', 'nav', 'aside']):
                element.decompose()

            # Enhanced text extraction with better structure preservation
            # First, try to find main content area
            main_content = None
            main_selectors = [
                'main', 'article', '.main-content', '.content',
                '.post-content', '.entry-content', '#content', '#main'
            ]

            for selector in main_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"Found main content using selector: {selector}")
                    break

            if main_content:
                # Extract text from main content area
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # Fallback to full page extraction with better cleaning
                # Remove more unwanted elements before extraction
                for element in soup.find_all(['script', 'style', 'noscript']):
                    element.decompose()

                # Get text with better separator handling
                text = soup.get_text(separator='\n', strip=True)

            # Post-process the extracted text
            text = clean_extracted_text(text)

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

def check_response_content(response):
    """Check if response content has any obvious issues"""
    logger.info(f"Checking response content...")

    # Check if content is empty
    if not response.content:
        logger.warning("Response content is empty")
        return False

    # Check if content is too short (might be an error page)
    if len(response.content) < 100:
        logger.warning(f"Response content is very short: {len(response.content)} bytes")
        return False

    # Check for common error indicators in content - be more specific
    error_indicators = [
        b'<title>Error</title>',
        b'<title>404</title>',
        b'<title>403</title>',
        b'<title>401</title>',
        b'<title>400</title>',
        b'HTTP Error',
        b'Page Not Found',
        b'Access Denied',
        b'Forbidden',
        b'Unauthorized'
    ]

    content_lower = response.content.lower()
    for indicator in error_indicators:
        if indicator.lower() in content_lower:
            logger.warning(f"Found specific error indicator in content: {indicator}")
            return False

    # Check if content looks like HTML
    if b'<!DOCTYPE' in content_lower or b'<html' in content_lower:
        logger.info("Content appears to be HTML")
        return True

    # Check if content might be compressed
    if response.headers.get('content-encoding'):
        logger.info(f"Content is encoded with: {response.headers.get('content-encoding')}")

    # Check for binary content indicators
    null_bytes = response.content.count(b'\x00')
    if null_bytes > len(response.content) * 0.1:  # More than 10% null bytes
        logger.warning(f"High number of null bytes detected: {null_bytes}")
        return False

    # If we get here, assume it's valid content
    logger.info("Content appears to be valid")
    return True

def is_readable_text(text):
    """Check if text appears to be readable (not garbled)"""
    if not text or len(text) < 10:
        return False

    # Count readable characters (letters, numbers, common punctuation)
    readable_chars = 0
    total_chars = len(text)

    for char in text:
        if char.isalnum() or char in ' .,!?;:()[]{}"\'-':
            readable_chars += 1

    # If less than 60% of characters are readable, likely garbled
    readability_ratio = readable_chars / total_chars
    is_readable = readability_ratio > 0.6

    logger.debug(f"Text readability: {readability_ratio:.2f} ({readable_chars}/{total_chars} chars)")

    # Additional check for common garbled patterns
    garbled_patterns = [
        'U™ØEUí‡»d@Õ¤',
        'â€™', 'â€œ', 'â€', 'Ã©', 'Ã¨', 'Ã ',
        'Ã¡', 'Ã­', 'Ã³', 'Ãº', 'Ã±', 'Ã§',
        'Ã¶', 'Ã¼', 'Ã¤', 'Ã¥', 'Ã¸', 'Ã¦'
    ]

    for pattern in garbled_patterns:
        if pattern in text:
            logger.debug(f"Found garbled pattern: {pattern}")
            return False

    return is_readable

def aggressive_text_cleaning(text):
    """Aggressively clean text to remove encoding artifacts"""
    if not text:
        return text

    # Remove all non-printable characters except newlines and tabs
    import re
    cleaned = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)

    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # Remove lines that are just special characters or numbers
    lines = cleaned.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip lines that are mostly special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', line)) / len(line)
        if special_char_ratio > 0.8:
            continue

        # Skip very short lines that are likely garbage
        if len(line) < 3:
            continue

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def clean_extracted_text(text):
    """Clean and improve extracted text content"""
    if not text:
        return text

    # Check for encoding issues (garbled text)
    if has_encoding_issues(text):
        logger.warning("Detected potential encoding issues in extracted text")
        # Try to fix encoding issues
        text = fix_encoding_issues(text)

    # Remove excessive whitespace and normalize line breaks
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Strip whitespace from each line
        line = line.strip()

        # Skip empty lines or lines with only special characters
        if not line or line.isspace():
            continue

        # Skip lines that are likely navigation or utility text
        if is_navigation_text(line):
            continue

        cleaned_lines.append(line)

    # Join lines with proper spacing
    cleaned_text = '\n'.join(cleaned_lines)

    # Remove excessive newlines (more than 2 consecutive)
    import re
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

    return cleaned_text.strip()

def has_encoding_issues(text):
    """Check if text has encoding issues (garbled characters)"""
    if not text:
        return False

    # Count non-printable and unusual characters
    unusual_chars = 0
    total_chars = len(text)

    for char in text:
        # Check for characters that are likely encoding errors
        if ord(char) > 127 and not char.isprintable():
            unusual_chars += 1
        # Check for common garbled character patterns
        elif char in '™ØEUí‡»d@Õ¤':
            unusual_chars += 1

    # If more than 10% of characters are unusual, likely has encoding issues
    if total_chars > 0 and (unusual_chars / total_chars) > 0.1:
        return True

    # Check for specific garbled patterns
    garbled_patterns = [
        'U™ØEUí‡»d@Õ¤',
        'â€™',  # Common UTF-8 encoding issue
        'â€œ',  # Common UTF-8 encoding issue
        'â€',   # Common UTF-8 encoding issue
        'Ã©',   # Common UTF-8 encoding issue
        'Ã¨',   # Common UTF-8 encoding issue
        'Ã ',   # Common UTF-8 encoding issue
    ]

    for pattern in garbled_patterns:
        if pattern in text:
            return True

    return False

def fix_encoding_issues(text):
    """Attempt to fix common encoding issues"""
    if not text:
        return text

    # Common UTF-8 encoding fixes
    encoding_fixes = {
        'â€™': "'",  # Right single quotation mark
        'â€œ': '"',  # Left double quotation mark
        'â€': '"',   # Right double quotation mark
        'Ã©': 'é',   # e with acute accent
        'Ã¨': 'è',   # e with grave accent
        'Ã ': 'à',   # a with grave accent
        'Ã¡': 'á',   # a with acute accent
        'Ã­': 'í',   # i with acute accent
        'Ã³': 'ó',   # o with acute accent
        'Ãº': 'ú',   # u with acute accent
        'Ã±': 'ñ',   # n with tilde
        'Ã§': 'ç',   # c with cedilla
        'Ã¶': 'ö',   # o with diaeresis
        'Ã¼': 'ü',   # u with diaeresis
        'Ã¤': 'ä',   # a with diaeresis
        'Ã¥': 'å',   # a with ring above
        'Ã¸': 'ø',   # o with stroke
        'Ã¦': 'æ',   # ae ligature
    }

    # Apply fixes
    for garbled, correct in encoding_fixes.items():
        text = text.replace(garbled, correct)

    # Remove any remaining non-printable characters
    import re
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)

    return text

def is_navigation_text(text):
    """Check if text is likely navigation or utility content"""
    if not text:
        return True

    # Common navigation/utility patterns
    navigation_patterns = [
        r'^\s*(Home|About|Contact|Services|News|Events|Donate|Volunteer)\s*$',
        r'^\s*(Menu|Search|Login|Sign up|Subscribe|Follow us)\s*$',
        r'^\s*(Facebook|Twitter|Instagram|YouTube|LinkedIn)\s*$',
        r'^\s*(Copyright|All rights reserved|Privacy Policy|Terms of Service)\s*$',
        r'^\s*[0-9]+\s*$',  # Just numbers
        r'^\s*[A-Z\s]+\s*$',  # All caps text (often navigation)
    ]

    import re
    for pattern in navigation_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True

    # Check for very short text that's likely navigation
    if len(text.strip()) <= 3 and text.strip().isupper():
        return True

    return False

# Get all documents from the collection
try:
    logger.info("Starting to stream documents from 'schemes' collection.")

    # Testing configuration - set to True to only process specific documents
    TESTING_MODE = False
    # doc_ids = ["4oE8YsKaFqa69HHFsAao", "5uYva3ETk2IQ85yyoD2a", "8tWBA0cWcJaDRuoBLQnj", "9lfZMJ0ZAiLhZeWRXV99", "AFT326wEDwbZtYy1356A", "BBnps4FBmDd4IEehux5i", "BlxfZvWnR4exdhVCLqHx" , "C8uVwKtjc2MwJSK60r4U", "CbwPvFgJ0cf1qgEoLNjy", "ESkFg9BNa2emqHYV3a9h", "FwpZNF9aCe4MfPmKUP4S", "IVTZrp8zeTbuLgec60bG", "IhKLeOTlBTc8tSkAgKEP", "IphFEQwQumWuEyDOiNPS", "LA6CzDU0EhOaHZW40jPL"]
    # doc_ids = ["Dsq1hv34RYgJGrY5hO6k"]
    # doc_ids = [
    # "ZnaaI9wPZ0M4bKxzqz7Z",
    # "mzq9kSFYoa9nJRSjo8mi",
    # "ke29dhM9VP7exsyMHBdR",
    # "5eAVPDSsy8G2CXE6YDzX",
    # "QEF7t67nTnTkYmPrcA5X",
    # "QMeMEyQ79DmOcbtN2ucH",
    # "WtqBqKnnniJyAhNjbA83",
    # "ZoPSL37hjD98SzoeL3oE",
    # "c5A5qMjY4GRzbnfbFEeQ",
    # "l8CmX6ZKXxQi1V8nFDZ4",
    # "mzq9kSFYoa9nJRSjo8mi",
    # "n1JVQhzmWsrqRAxg93nA",
    # "o937Z2wTY4kn1Js7VH0L",
    # "rCWgF4B65MCBsvt7JHSI",
    # "uL9vy6RlHcjBGkXqYn39",
    # "vFNkWq8MQBcLrK9cTdPk"
    # ]
    #Doc ids for new schemes from carecorner - 13 July
    # doc_ids = ["S6easrpcSTJOmXhCvG9F", "BcXpy7bOUjDyOrkB3WmU", "yZtyMYNs7xsVu4ilHOmM", "r0cZr6LdA4Ha2abPr4aG", "Q49szphEOJPmsqT2DXP5"]

    if TESTING_MODE:
        # For testing: only process specific document IDs
        logger.info(f"Testing mode: Processing only {len(doc_ids)} specific documents")

        # Get only the specified documents instead of streaming all
        docs_to_process = []
        for doc_id in doc_ids:
            try:
                doc = db.collection("schemes").document(doc_id).get()
                if doc.exists:
                    docs_to_process.append(doc)
                    logger.info(f"Found document {doc_id} for processing")
                else:
                    logger.warning(f"Document {doc_id} not found in collection")
            except Exception as e:
                logger.error(f"Error fetching document {doc_id}: {e}")
                continue
    else:
        # Production mode: process all documents
        logger.info("Production mode: Processing all documents in collection")
        docs_to_process = db.collection("schemes").stream()

    # Set the flag to control scraping behavior (No longer used for skipping, but kept for potential future use)
    skip_if_scraped = False # Consider making this an argument if needed frequently

    for doc in docs_to_process:
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
            should_skip_scraping = skip_if_scraped and bool(doc_data.get("scraped_text"))
            if TESTING_MODE:
                should_skip_scraping = False

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
