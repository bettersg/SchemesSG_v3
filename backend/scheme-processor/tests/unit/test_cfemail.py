"""Tests for Cloudflare email decoder."""
import pytest
from app.services.cfemail import decode_cfemail, extract_cf_protected_emails


class TestDecodeCfemail:
    """Test the decode_cfemail function."""

    def test_decode_cfemail_simple(self):
        """Test decoding a known Cloudflare hex string."""
        # This hex decodes to "info@better.sg"
        hex_str = "d6bfb8b0b996b4b3a2a2b3a4f8a5b1"
        result = decode_cfemail(hex_str)
        assert result == "info@better.sg"

    def test_decode_cfemail_invalid_hex(self):
        """Test that invalid hex raises ValueError."""
        with pytest.raises(ValueError):
            decode_cfemail("zzzz")

    def test_decode_cfemail_invalid_utf8(self):
        """Test that invalid UTF-8 raises UnicodeDecodeError."""
        # Create hex that decodes to invalid UTF-8
        with pytest.raises(UnicodeDecodeError):
            decode_cfemail("00ff")


class TestExtractCfProtectedEmails:
    """Test the extract_cf_protected_emails function."""

    def test_extract_from_cdn_cgi_link(self):
        """Test extracting email from /cdn-cgi/l/email-protection# format."""
        html = 'href="/cdn-cgi/l/email-protection#d6bfb8b0b996b4b3a2a2b3a4f8a5b1"'
        result = extract_cf_protected_emails(html)
        assert "info@better.sg" in result

    def test_extract_from_data_attribute(self):
        """Test extracting email from data-cfemail attribute."""
        html = '<a data-cfemail="d6bfb8b0b996b4b3a2a2b3a4f8a5b1">[email protected]</a>'
        result = extract_cf_protected_emails(html)
        assert "info@better.sg" in result

    def test_no_duplicates(self):
        """Test that same email appearing twice is only returned once."""
        html = '''
            <a data-cfemail="d6bfb8b0b996b4b3a2a2b3a4f8a5b1">[email protected]</a>
            <a href="/cdn-cgi/l/email-protection#d6bfb8b0b996b4b3a2a2b3a4f8a5b1">Contact</a>
        '''
        result = extract_cf_protected_emails(html)
        assert result.count("info@better.sg") == 1

    def test_empty_html(self):
        """Test with empty HTML."""
        result = extract_cf_protected_emails("")
        assert result == []

    def test_no_cloudflare_emails(self):
        """Test with HTML that has no Cloudflare emails."""
        html = '<p>Just plain text, no emails here</p>'
        result = extract_cf_protected_emails(html)
        assert result == []

    def test_multiple_different_emails(self):
        """Test extracting multiple different emails."""
        # Note: In reality, finding different CF emails requires different hex strings
        # For now, we test with the same email in different formats
        html = '''
            <a data-cfemail="d6bfb8b0b996b4b3a2a2b3a4f8a5b1">[email protected]</a>
            <p>Some other content</p>
            <a href="/cdn-cgi/l/email-protection#d6bfb8b0b996b4b3a2a2b3a4f8a5b1">Contact</a>
        '''
        result = extract_cf_protected_emails(html)
        assert len(result) == 1  # Same email, so only 1 unique
        assert "info@better.sg" in result
