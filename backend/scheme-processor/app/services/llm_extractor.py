"""
LLM field extraction using Azure OpenAI.

Extracts structured data from scraped web content.
"""

import json
import os
import re
from typing import Any, Dict

from app.constants import (
    EXTRACTION_INSTRUCTION,
    SCHEME_TYPE,
    WHAT_IT_GIVES,
    WHO_IS_IT_FOR,
)
from app.services.extraction import is_generic_email, normalize_categories
from loguru import logger


def _configure_litellm():
    """Configure LiteLLM to avoid event loop conflicts."""
    import litellm

    litellm.modify_params = True
    litellm.drop_params = True
    litellm.set_verbose = False
    os.environ["LITELLM_LOG"] = "ERROR"


# Run configuration once at module load
_configure_litellm()

_HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")


def _strip_code_fences(text: str) -> str:
    """Strip markdown code fences from LLM response."""
    text = text.strip()
    # Try ```json ... ``` first
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If it starts/ends with ``` without language tag
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def extract_with_llm(content: str) -> Dict[str, Any]:
    """
    Extract structured fields from content using Azure OpenAI.

    Args:
        content: Scraped text content (HTML or plain text)

    Returns:
        Dict with extracted fields
    """
    if not content or len(content) < 100:
        return {}

    try:
        import litellm

        # Get Azure config from environment
        azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        azure_base = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        azure_version = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5")

        if not azure_key or not azure_base:
            logger.warning("Azure OpenAI not configured, skipping LLM extraction")
            return {}

        # Set env vars for LiteLLM
        os.environ["AZURE_API_KEY"] = azure_key
        os.environ["AZURE_API_BASE"] = azure_base
        os.environ["AZURE_API_VERSION"] = azure_version

        # Convert HTML to clean text if needed (check for actual HTML tags)
        if _HTML_TAG_RE.search(content):
            logger.info(f"Converting {len(content)} chars of HTML to clean text")
            text = _html_to_text(content)
            logger.info(f"Converted to {len(text)} chars of clean text")
        else:
            text = content

        if len(text) < 50:
            logger.warning("Clean text too short after conversion")
            return {}

        # Smart truncation: keep first 10K + last 2K to preserve footer/contact info
        max_chars = 12000
        if len(text) > max_chars:
            head_size = 10000
            tail_size = 2000
            truncated_text = text[:head_size] + "\n\n[...truncated...]\n\n" + text[-tail_size:]
        else:
            truncated_text = text

        # Build extraction prompt with full category lists
        prompt = f"""{EXTRACTION_INSTRUCTION}

Content to extract from:
---
{truncated_text}
---

Return a JSON object with these fields:
- llm_description: A comprehensive description of the scheme/service using newlines and bullet point lists for readability. Do NOT duplicate information from the eligibility, how_to_apply, or agency fields. Focus on what the scheme does, who it helps, and key benefits.
- summary: A brief 1-2 sentence summary (string)
- eligibility: Eligibility criteria and requirements (string)
- how_to_apply: Steps to apply for this scheme (string)
- agency: The organization name providing this scheme (string)
- address: Full physical address including postal code if available (string)
- phone: Phone number(s) found on the page, including hotlines and toll-free numbers. Comma-separated if multiple (string or null)
- email: Contact email address(es) found on the page. Comma-separated if multiple (string or null)
- who_is_it_for: Target audiences as array, select ONLY from: {", ".join(WHO_IS_IT_FOR)}
- what_it_gives: Benefits/services as array, select ONLY from: {", ".join(WHAT_IT_GIVES)}
- scheme_type: Scheme categories as array, select ONLY from: {", ".join(SCHEME_TYPE)}
- service_area: Geographic service area (string)
- search_booster: Comma-separated keywords for search (string)

Return ONLY valid JSON, no markdown code blocks or explanation."""

        logger.info("Calling Azure OpenAI for extraction...")

        # Retry once for transient API errors
        last_error = None
        for attempt in range(2):
            try:
                response = litellm.completion(
                    model=f"azure/{deployment_name}",
                    messages=[{"role": "user", "content": prompt}],
                    api_key=azure_key,
                    api_base=azure_base,
                    api_version=azure_version,
                    max_tokens=3000,
                    reasoning_effort="low",
                )
                break
            except Exception as api_err:
                last_error = api_err
                err_str = str(api_err).lower()
                if attempt == 0 and ("timeout" in err_str or "rate" in err_str or "429" in err_str):
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying: {api_err}")
                    import asyncio
                    await asyncio.sleep(2)
                    continue
                raise
        else:
            raise last_error

        response_content = response.choices[0].message.content or ""
        logger.info(f"LLM extraction response: {len(response_content)} chars")
        if not response_content:
            logger.error(f"Empty response from LLM. Usage: {response.usage}")
            return {}

        # Parse JSON from response (robust code fence stripping)
        response_content = _strip_code_fences(response_content)
        extracted = json.loads(response_content.strip())

        # Normalize categories
        who_is_it_for = normalize_categories(
            extracted.get("who_is_it_for") if isinstance(extracted.get("who_is_it_for"), list) else [], WHO_IS_IT_FOR
        )
        what_it_gives = normalize_categories(
            extracted.get("what_it_gives") if isinstance(extracted.get("what_it_gives"), list) else [], WHAT_IT_GIVES
        )
        scheme_type = normalize_categories(
            extracted.get("scheme_type") if isinstance(extracted.get("scheme_type"), list) else [], SCHEME_TYPE
        )

        # Extract and filter phone/email from LLM (fallback for regex)
        llm_phone = extracted.get("phone")
        llm_email = extracted.get("email")

        # Filter generic/placeholder emails from LLM output
        if llm_email and isinstance(llm_email, str):
            filtered = [e.strip() for e in llm_email.split(",") if not is_generic_email(e.strip())]
            llm_email = ", ".join(filtered) if filtered else None

        result = {
            "address": extracted.get("address"),
            "phone": llm_phone,
            "email": llm_email,
            "llm_description": extracted.get("llm_description"),
            "summary": extracted.get("summary"),
            "eligibility": extracted.get("eligibility"),
            "how_to_apply": extracted.get("how_to_apply"),
            "agency": extracted.get("agency"),
            "who_is_it_for": who_is_it_for if who_is_it_for else None,
            "what_it_gives": what_it_gives if what_it_gives else None,
            "scheme_type": scheme_type if scheme_type else None,
            "service_area": extracted.get("service_area"),
            "search_booster": extracted.get("search_booster"),
        }

        logger.info(
            f"Extraction successful: agency={result.get('agency')}, "
            f"summary={result.get('summary')[:50] if result.get('summary') else 'None'}..."
        )
        return result

    except json.JSONDecodeError as je:
        logger.error(f"Failed to parse LLM JSON response: {je}")
        return {}
    except Exception as e:
        logger.error(f"LLM extraction error: {e}")
        import traceback

        traceback.print_exc()
        return {}


def _html_to_text(html: str) -> str:
    """Convert HTML to clean text, removing scripts, styles, and noise."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "noscript", "iframe", "svg"]):
        element.decompose()

    # Get text content
    text = soup.get_text(separator="\n", strip=True)

    # Clean up multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text
