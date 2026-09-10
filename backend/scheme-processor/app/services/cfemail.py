"""Decode Cloudflare-obfuscated emails (data-cfemail)."""
import re
from typing import List

# Pattern to find Cloudflare-protected emails in HTML
CFEMAIL_HEX = re.compile(
    r'(?:data-cfemail="|/cdn-cgi/l/email-protection#)([0-9a-fA-F]{4,})'
)


def decode_cfemail(hex_str: str) -> str:
    """
    Decode a Cloudflare cfemail hex string.
    
    How it works:
    - First byte of hex is the XOR key
    - Rest of the bytes are XOR-encoded with that key
    - We reverse the XOR to get the real email
    
    Args:
        hex_str: The hex string from data-cfemail attribute
        
    Returns:
        The decoded email address (e.g., "info@charity.org")
    """
    # Convert hex string to bytes
    data = bytes.fromhex(hex_str)
    
    # First byte is the key
    key = data[0]
    
    # XOR every other byte with the key to decode
    decoded_bytes = bytes(b ^ key for b in data[1:])
    
    # Convert bytes back to text
    return decoded_bytes.decode("utf-8")


def extract_cf_protected_emails(html: str) -> List[str]:
    """
    Find and decode all Cloudflare-protected emails in raw HTML.
    
    Args:
        html: Raw HTML source code
        
    Returns:
        List of decoded email addresses, with duplicates removed
    """
    emails = []
    
    # Find all matches of the hex pattern
    for match in CFEMAIL_HEX.finditer(html):
        try:
            # Try to decode this match
            decoded = decode_cfemail(match.group(1))
            
            # Only add if it looks like an email and we haven't seen it before
            if "@" in decoded and decoded not in emails:
                emails.append(decoded)
        except (ValueError, UnicodeDecodeError):
            # If decoding fails, just skip this one
            continue
    
    return emails
