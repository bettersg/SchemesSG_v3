"""
LLM field extraction using Azure OpenAI.

Extracts structured data from scraped web content.
"""
import os
import re
import json
from typing import Dict, Any

from loguru import logger

from app.constants import (
    WHO_IS_IT_FOR,
    WHAT_IT_GIVES,
    SCHEME_TYPE,
    EXTRACTION_INSTRUCTION,
)
from app.services.extraction import normalize_categories


def _configure_litellm():
    """Configure LiteLLM to avoid event loop conflicts."""
    import litellm
    litellm.modify_params = True
    litellm.drop_params = True
    litellm.set_verbose = False
    os.environ["LITELLM_LOG"] = "ERROR"


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

    _configure_litellm()

    try:
        import litellm

        # Get Azure config from environment
        azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        azure_base = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        azure_version = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

        if not azure_key or not azure_base:
            logger.warning("Azure OpenAI not configured, skipping LLM extraction")
            return {}

        # Set env vars for LiteLLM
        os.environ["AZURE_API_KEY"] = azure_key
        os.environ["AZURE_API_BASE"] = azure_base
        os.environ["AZURE_API_VERSION"] = azure_version

        # Convert HTML to clean text if needed
        if '<' in content and '>' in content:
            logger.info(f"Converting {len(content)} chars of HTML to clean text")
            text = _html_to_text(content)
            logger.info(f"Converted to {len(text)} chars of clean text")
        else:
            text = content

        if len(text) < 50:
            logger.warning("Clean text too short after conversion")
            return {}

        # Truncate if too long
        max_chars = 12000
        truncated_text = text[:max_chars] if len(text) > max_chars else text

        # Build extraction prompt
        prompt = f"""{EXTRACTION_INSTRUCTION}

Content to extract from:
---
{truncated_text}
---

Return a JSON object with these fields:
- llm_description: A comprehensive description of the scheme/service (string)
- summary: A brief 1-2 sentence summary (string)
- eligibility: Eligibility criteria and requirements (string)
- how_to_apply: Steps to apply for this scheme (string)
- agency: The organization name providing this scheme (string)
- address: Full physical address including postal code if available (string)
- who_is_it_for: Target audiences as array, select from: {', '.join(WHO_IS_IT_FOR[:15])}...
- what_it_gives: Benefits/services as array, select from: {', '.join(WHAT_IT_GIVES[:15])}...
- scheme_type: Scheme categories as array, select from: {', '.join(SCHEME_TYPE[:10])}...
- service_area: Geographic service area (string)
- search_booster: Comma-separated keywords for search (string)

Return ONLY valid JSON, no markdown code blocks or explanation."""

        logger.info("Calling Azure OpenAI for extraction...")
        response = litellm.completion(
            model=f"azure/{deployment_name}",
            messages=[{"role": "user", "content": prompt}],
            api_key=azure_key,
            api_base=azure_base,
            api_version=azure_version,
            temperature=0,
            max_tokens=2000
        )

        response_content = response.choices[0].message.content
        logger.info(f"LLM extraction response: {len(response_content)} chars")

        # Parse JSON from response
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0]
        elif "```" in response_content:
            response_content = response_content.split("```")[1].split("```")[0]

        extracted = json.loads(response_content.strip())

        # Normalize categories
        who_is_it_for = normalize_categories(
            extracted.get("who_is_it_for") if isinstance(extracted.get("who_is_it_for"), list) else [],
            WHO_IS_IT_FOR
        )
        what_it_gives = normalize_categories(
            extracted.get("what_it_gives") if isinstance(extracted.get("what_it_gives"), list) else [],
            WHAT_IT_GIVES
        )
        scheme_type = normalize_categories(
            extracted.get("scheme_type") if isinstance(extracted.get("scheme_type"), list) else [],
            SCHEME_TYPE
        )

        result = {
            "address": extracted.get("address"),
            "phone": None,  # Filled by regex (more reliable)
            "email": None,  # Filled by regex (more reliable)
            "llm_description": extracted.get("llm_description"),
            "summary": extracted.get("summary"),
            "eligibility": extracted.get("eligibility"),
            "how_to_apply": extracted.get("how_to_apply"),
            "agency": extracted.get("agency"),
            "who_is_it_for": ", ".join(who_is_it_for) if who_is_it_for else None,
            "what_it_gives": ", ".join(what_it_gives) if what_it_gives else None,
            "scheme_type": ", ".join(scheme_type) if scheme_type else None,
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

    soup = BeautifulSoup(html, 'lxml')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'noscript', 'iframe', 'svg']):
        element.decompose()

    # Get text content
    text = soup.get_text(separator='\n', strip=True)

    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text
