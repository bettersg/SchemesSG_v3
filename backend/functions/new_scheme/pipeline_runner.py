"""
Lightweight Pipeline Runner for New Scheme Processing.

Uses crawl4ai for web crawling and LLM extraction.

Runs pipeline steps 1-4 for a single user-submitted scheme:
1. Crawl website content (with shallow deep crawl)
2. Extract LLM fields (description, eligibility, who_is_it_for, etc.)
3. Extract contact info via regex (more reliable for emails/phones)
4. Extract town/planning area from address

Skips steps 5-7 (ChromaDB and model artifacts).
"""
import os
import re
import io
import json
import asyncio
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


# Constants for categorization (simplified from dataset_workflow/src/constants.py)
WHO_IS_IT_FOR = [
    "Children", "Youth", "Youth-at-risk", "Teenagers facing pregnancy", "Young adults",
    "Students", "Families", "Single parents", "Women", "Pregnant individuals in distress",
    "Elderly", "Elderly with dementia", "Persons with disabilities (PWDs)",
    "Persons with special needs", "Persons on autism spectrum",
    "Persons with chronic or terminal illnesses", "Persons with mental health issues",
    "Caregivers", "Low income", "Low income families", "Low income elderly",
    "Unemployed", "Retrenched", "Homeless", "Need shelter", "Need food support",
    "Foreign domestic workers/maids", "Migrant workers/Foreign workers", "Ex-offenders",
    "Inmates", "Families of inmates or ex-offenders", "Victims of abuse or harassment",
    "Facing end of life", "Facing financial hardship", "Need mortgage support",
    "Individuals needing legal aid", "Individuals struggling with loss",
    "Individuals with gambling addiction", "Transnational families/Foreign spouses",
    "Malay/Muslim community", "Indian community", "Chinese community", "General public"
]

WHAT_IT_GIVES = [
    "Counselling", "Casework", "Emotional care", "Mental health assessment and treatment",
    "Psychological support/Psychotherapy", "Befriending services", "Helpline services",
    "Referral services", "Educational programmes", "Vocational training",
    "Employment assistance", "Skills training and job matching",
    "Financial assistance (general)", "Financial assistance for daily living expenses",
    "Financial assistance for healthcare", "Financial assistance for education",
    "Financial assistance for housing", "Food support", "Housing/Shelter",
    "Respite care/Caregiver support", "Child protection services", "Childcare services",
    "Transport subsidies", "Healthcare (general/basic services)", "Dental services",
    "Rehabilitation services", "Legal aid and services", "Protection against violence",
    "Residential care/programmes", "Support groups", "Bereavement support",
    "End-of-life care", "Technology assistance", "Information services"
]

SCHEME_TYPE = [
    "Low Income", "Family", "Children", "Youth", "Youth-at-Risk", "Women",
    "Single Parents", "Elderly", "Caregiver Support", "Persons with Disabilities (PWD)",
    "Special Needs", "Ex-offender Support", "Education Support", "Healthcare",
    "Mental Health", "End-of-Life/Palliative Care", "Food Support", "Housing/Shelter",
    "Employment Support", "Vocational Training", "Financial Assistance",
    "Transport Support", "Legal Aid", "Abuse/Family Violence", "COVID-19 Support",
    "Counselling and Emotional Support", "General Public Support"
]

# Logo detection patterns
LOGO_PATTERNS = ['logo', 'brand', 'icon', 'emblem']
HEADER_PATTERNS = ['header', 'nav', 'navbar', 'footer', 'masthead', 'top-bar', 'topbar']
NEGATIVE_PATTERNS = ['banner', 'hero', 'background', 'social', 'facebook', 'twitter', 'linkedin', 'instagram', 'youtube', 'ad-', 'promo', 'slider', 'carousel', 'gallery', 'thumbnail', 'avatar', 'profile']

# LLM extraction instruction
EXTRACTION_INSTRUCTION = """You are an expert extraction algorithm for Singapore social service schemes.
Extract the requested attributes accurately from the given website text.

For who_is_it_for: select ALL applicable values from the allowed options that describe the target audience.
For what_it_gives: select ALL applicable values from the allowed options that describe the benefits/services provided.
For scheme_type: select ALL applicable values from the allowed options that categorize this scheme.

For agency: extract the organization name that provides this scheme/service.
For search_booster: generate relevant keywords that people might use to search for this scheme (comma-separated).

If a value cannot be determined from the content, return null for that field."""


def is_emulator_mode() -> bool:
    """Check if running in Firebase emulator mode."""
    return os.getenv("FIRESTORE_EMULATOR_HOST") is not None


class PhysicalLocation(BaseModel):
    """Represents a physical location with its contact information."""
    location_name: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)


class SchemesStructuredOutput(BaseModel):
    """Schema for LLM extraction - matches Firestore schemes collection."""
    # Contact info
    physical_locations: Optional[List[PhysicalLocation]] = Field(default=None)

    # Core fields
    llm_description: Optional[str] = Field(
        default=None,
        description="A comprehensive description of the scheme/service"
    )
    summary: Optional[str] = Field(
        default=None,
        description="A brief 1-2 sentence summary of the scheme"
    )
    eligibility: Optional[str] = Field(
        default=None,
        description="Eligibility criteria and requirements"
    )
    how_to_apply: Optional[str] = Field(
        default=None,
        description="Steps to apply for this scheme"
    )
    agency: Optional[str] = Field(
        default=None,
        description="The organization name providing this scheme"
    )

    # Categorization
    who_is_it_for: Optional[List[str]] = Field(
        default=None,
        description=f"Select from: {', '.join(WHO_IS_IT_FOR)}"
    )
    what_it_gives: Optional[List[str]] = Field(
        default=None,
        description=f"Select from: {', '.join(WHAT_IT_GIVES)}"
    )
    scheme_type: Optional[List[str]] = Field(
        default=None,
        description=f"Select from: {', '.join(SCHEME_TYPE)}"
    )

    # Additional fields
    service_area: Optional[str] = Field(
        default=None,
        description="Geographic service area or boundaries"
    )
    search_booster: Optional[str] = Field(
        default=None,
        description="Comma-separated keywords for search optimization"
    )


def extract_contact_info_regex(text: str) -> Dict[str, List[str]]:
    """
    Extract contact info using regex patterns - more reliable than LLM for emails/phones.
    Returns dict with 'emails', 'phones', 'addresses' lists.
    """
    results = {'emails': [], 'phones': [], 'addresses': []}

    # Email regex - standard pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    # Filter out common false positives
    filtered_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.gif', '.css', '.js'))]
    results['emails'] = list(dict.fromkeys(filtered_emails))  # Dedupe

    # Singapore phone patterns: +65 XXXX XXXX, 6XXX XXXX, 8XXX XXXX, 9XXX XXXX
    phone_patterns = [
        r'\+65[\s\-]?\d{4}[\s\-]?\d{4}',  # +65 format
        r'\(65\)[\s\-]?\d{4}[\s\-]?\d{4}',  # (65) format
        r'(?<!\d)[689]\d{3}[\s\-]?\d{4}(?!\d)',  # Local 8-digit (6/8/9 prefix)
        r'1800[\s\-]?\d{3}[\s\-]?\d{4}',  # Toll-free 1800
        r'1900[\s\-]?\d{3}[\s\-]?\d{4}',  # Premium 1900
    ]
    phones = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    # Clean and dedupe
    cleaned_phones = [re.sub(r'[\s\-]', '', p) for p in phones]
    results['phones'] = list(dict.fromkeys(cleaned_phones))

    # Singapore postal code pattern (6 digits)
    postal_pattern = r'Singapore\s*\d{6}|S\s*\(\s*\d{6}\s*\)|S\d{6}'
    postal_matches = re.findall(postal_pattern, text, re.IGNORECASE)
    results['addresses'] = list(dict.fromkeys(postal_matches))

    return results


def map_to_valid_values(llm_values: Optional[List[str]], valid_options: List[str]) -> List[str]:
    """Map LLM output values to valid options using keyword matching."""
    if not llm_values:
        return []

    stop_words = {"and", "or", "the", "a", "an", "for", "of", "in", "to", "with"}

    def get_keywords(text: str) -> set:
        words = text.lower().replace("/", " ").replace("-", " ").split()
        return {w for w in words if w not in stop_words and len(w) > 2}

    mapped = []
    for llm_val in llm_values:
        llm_lower = llm_val.lower().strip()
        llm_keywords = get_keywords(llm_val)

        # Try exact match first
        for opt in valid_options:
            if llm_lower == opt.lower():
                mapped.append(opt)
                break
        else:
            # Try keyword overlap
            for opt in valid_options:
                opt_keywords = get_keywords(opt)
                if llm_keywords & opt_keywords:
                    mapped.append(opt)
                    break

    return list(dict.fromkeys(mapped))  # Remove duplicates, preserve order


def select_best_logo(images: List[Dict], base_url: str = "") -> Optional[str]:
    """Select the best logo image from crawl4ai results."""
    if not images:
        return None

    best_score = -1
    best_url = None

    for img in images:
        src = img.get('src', '')
        if not src or src.startswith('data:'):
            continue

        src_lower = src.lower()
        alt_lower = img.get('alt', '').lower()
        desc_lower = img.get('desc', '').lower()
        score = img.get('score', 0) or 0

        # Strong boost for logo patterns in URL or alt
        if any(p in src_lower or p in alt_lower for p in LOGO_PATTERNS):
            score += 20

        # Boost for header/footer/nav location (check URL, alt, and desc)
        if any(p in src_lower or p in alt_lower or p in desc_lower for p in HEADER_PATTERNS):
            score += 15

        # Boost for SVG (common logo format)
        if '.svg' in src_lower:
            score += 10

        # Small boost for PNG with transparency (common for logos)
        if '.png' in src_lower:
            score += 3

        # Penalty for non-logo patterns
        if any(p in src_lower or p in alt_lower for p in NEGATIVE_PATTERNS):
            score -= 25

        if score > best_score:
            best_score = score
            best_url = src

    # Convert relative URL to absolute
    if best_url and base_url and not best_url.startswith(('http://', 'https://')):
        best_url = urljoin(base_url, best_url)

    logger.info(f"Logo selection: score={best_score}, url={best_url[:80] if best_url else 'None'}...")
    return best_url if best_score > 0 else None


class Crawl4AIProcessor:
    """Unified crawl and extract using crawl4ai."""

    def __init__(self):
        self._setup_azure_env()

    def _setup_azure_env(self):
        """Map current env vars to LiteLLM expected names."""
        # LiteLLM expects these specific env var names for Azure
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_base = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_version = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

        logger.info(f"Azure config - key present: {bool(self.azure_key)}, base: {self.azure_base[:30] if self.azure_base else 'None'}..., deployment: {self.deployment_name}")

        # Set env vars for LiteLLM
        if self.azure_key:
            os.environ["AZURE_API_KEY"] = self.azure_key
        if self.azure_base:
            os.environ["AZURE_API_BASE"] = self.azure_base
        if self.azure_version:
            os.environ["AZURE_API_VERSION"] = self.azure_version

    def _create_llm_config(self):
        """Create LLMConfig for Azure OpenAI."""
        from crawl4ai import LLMConfig

        return LLMConfig(
            provider=f"azure/{self.deployment_name}",
            api_token=self.azure_key,
            base_url=self.azure_base,
            temperature=0,
            max_tokens=4000
        )

    def _create_extraction_strategy(self):
        """Create LLMExtractionStrategy with Pydantic schema."""
        from crawl4ai import LLMExtractionStrategy

        return LLMExtractionStrategy(
            llm_config=self._create_llm_config(),
            schema=SchemesStructuredOutput.model_json_schema(),
            extraction_type="schema",
            instruction=EXTRACTION_INSTRUCTION,
            apply_chunking=True,
            chunk_token_threshold=4000,
            input_format="markdown",
            extra_args={"temperature": 0}
        )

    async def process_url(self, url: str) -> Tuple[str, Dict[str, Any], Optional[str]]:
        """
        Crawl URL with shallow deep crawl and extract structured data.

        Returns:
            Tuple of (scraped_text, llm_fields, logo_url)
        """
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        # Check if PDF - handle separately
        if url.lower().endswith('.pdf'):
            logger.info(f"PDF detected, using fallback extraction: {url}")
            pdf_text = self._extract_pdf_from_url(url)
            if pdf_text.startswith("PDF") and "Error" in pdf_text:
                return pdf_text, self._empty_result(), None
            # For PDFs, do simple LLM extraction without crawl4ai
            llm_fields = await self._extract_from_text(pdf_text)
            return pdf_text, llm_fields, None

        try:
            # Create extraction strategy
            extraction_strategy = self._create_extraction_strategy()

            # Configure browser for headless crawling
            browser_config = BrowserConfig(headless=True)

            # Configure shallow deep crawl
            crawl_config = CrawlerRunConfig(
                deep_crawl_strategy=BFSDeepCrawlStrategy(
                    max_depth=1,  # Main page + direct links
                    include_external=False,  # Stay on same domain
                    max_pages=5  # Limit pages to avoid long processing
                ),
                extraction_strategy=extraction_strategy,
                cache_mode=CacheMode.BYPASS,
                verbose=False
            )

            logger.info(f"Starting crawl4ai deep crawl for: {url}")

            async with AsyncWebCrawler(config=browser_config) as crawler:
                results = await crawler.arun(url=url, config=crawl_config)

            # Handle results (can be single result or list for deep crawl)
            if not results:
                logger.warning(f"No results from crawl4ai for: {url}")
                return "Crawl Error: No results", self._empty_result(), None

            # Process results
            if isinstance(results, list):
                all_text = []
                all_extracted = []
                logo_url = None

                for result in results:
                    if result.success:
                        # Collect text
                        text = result.markdown or result.cleaned_html or ""
                        if text:
                            all_text.append(text)

                        # Collect extracted content
                        if result.extracted_content:
                            try:
                                extracted = json.loads(result.extracted_content)
                                if isinstance(extracted, list):
                                    all_extracted.extend(extracted)
                                else:
                                    all_extracted.append(extracted)
                            except json.JSONDecodeError:
                                pass

                        # Get logo from first successful result
                        if not logo_url and hasattr(result, 'media') and result.media:
                            images = result.media.get('images', [])
                            if images:
                                logo_url = select_best_logo(images, url)

                scraped_text = "\n\n---PAGE BREAK---\n\n".join(all_text)
                llm_fields = self._merge_extracted_results(all_extracted)

            else:
                # Single result
                result = results
                if not result.success:
                    error_msg = result.error_message or "Unknown crawl error"
                    logger.error(f"Crawl failed: {error_msg}")
                    return f"Crawl Error: {error_msg}", self._empty_result(), None

                scraped_text = result.markdown or result.cleaned_html or ""
                logo_url = None

                if hasattr(result, 'media') and result.media:
                    images = result.media.get('images', [])
                    if images:
                        logo_url = select_best_logo(images, url)

                # Parse extracted content
                llm_fields = self._empty_result()
                if result.extracted_content:
                    try:
                        extracted = json.loads(result.extracted_content)
                        if isinstance(extracted, list) and extracted:
                            llm_fields = self._transform_extracted(extracted[0])
                        elif isinstance(extracted, dict):
                            llm_fields = self._transform_extracted(extracted)
                    except json.JSONDecodeError:
                        pass

            logger.info(f"Crawl4ai completed for {url}: {len(scraped_text)} chars")
            return scraped_text, llm_fields, logo_url

        except Exception as e:
            logger.error(f"Crawl4ai error for {url}: {e}")
            return f"Crawl Error: {str(e)}", self._empty_result(), None

    async def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract fields from text using LLM (for PDFs)."""
        from crawl4ai import LLMExtractionStrategy

        if not text or len(text) < 50:
            return self._empty_result()

        try:
            strategy = self._create_extraction_strategy()
            # Manual extraction for text content
            extracted = strategy.extract(url="", content_chunk=text)
            if extracted and isinstance(extracted, list) and extracted:
                return self._transform_extracted(extracted[0])
            return self._empty_result()
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return self._empty_result()

    def _extract_pdf_from_url(self, url: str) -> str:
        """Download and extract text from PDF URL."""
        try:
            from pypdf import PdfReader
            response = requests.get(url, timeout=30, verify=False)
            response.raise_for_status()

            pdf_file = io.BytesIO(response.content)
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            return f"PDF Processing Error: {str(e)}"

    def _merge_extracted_results(self, extracted_list: List[Dict]) -> Dict[str, Any]:
        """Merge multiple extracted results into one."""
        if not extracted_list:
            return self._empty_result()

        if len(extracted_list) == 1:
            return self._transform_extracted(extracted_list[0])

        # Merge results - take first non-null value for each field
        merged = self._empty_result()
        for extracted in extracted_list:
            transformed = self._transform_extracted(extracted)
            for key, value in transformed.items():
                if value and not merged.get(key):
                    merged[key] = value

        return merged

    def _transform_extracted(self, extracted: Dict) -> Dict[str, Any]:
        """Transform extracted data to match expected output format."""
        if not extracted:
            return self._empty_result()

        # Handle physical locations
        address, phone, email = None, None, None
        physical_locations = extracted.get("physical_locations")
        if physical_locations:
            if len(physical_locations) == 1:
                loc = physical_locations[0]
                address = loc.get("address")
                phone = loc.get("phone")
                email = loc.get("email")
            elif len(physical_locations) > 1:
                addresses = [loc.get("address") for loc in physical_locations if loc.get("address")]
                phones = [loc.get("phone") for loc in physical_locations if loc.get("phone")]
                emails = [loc.get("email") for loc in physical_locations if loc.get("email")]
                address = ", ".join(addresses) if addresses else None
                phone = ", ".join(phones) if phones else None
                email = ", ".join(emails) if emails else None

        # Map categorization fields to valid values
        who_is_it_for = map_to_valid_values(extracted.get("who_is_it_for"), WHO_IS_IT_FOR)
        what_it_gives = map_to_valid_values(extracted.get("what_it_gives"), WHAT_IT_GIVES)
        scheme_type = map_to_valid_values(extracted.get("scheme_type"), SCHEME_TYPE)

        return {
            "address": address,
            "phone": phone,
            "email": email,
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

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result dict."""
        return {
            "address": None,
            "phone": None,
            "email": None,
            "llm_description": None,
            "summary": None,
            "eligibility": None,
            "how_to_apply": None,
            "agency": None,
            "who_is_it_for": None,
            "what_it_gives": None,
            "scheme_type": None,
            "service_area": None,
            "search_booster": None,
        }


class PlanningAreaExtractor:
    """Extract planning area from Singapore address using OneMap API."""

    def __init__(self):
        self.token = self._get_onemap_token()

    def _get_onemap_token(self) -> Optional[str]:
        """Get OneMap API access token."""
        email = os.getenv("ONEMAP_EMAIL")
        password = os.getenv("ONEMAP_EMAIL_PASSWORD")

        if not email or not password:
            logger.warning("OneMap credentials not configured")
            return None

        try:
            response = requests.post(
                "https://www.onemap.gov.sg/api/auth/post/getToken",
                json={"email": email, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.warning(f"OneMap auth failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to get OneMap token: {e}")

        return None

    def extract_planning_area(self, address: str) -> Optional[str]:
        """Extract planning area from address."""
        if not address or not self.token:
            return None

        try:
            # Extract postal code if present
            postal_match = re.search(r'\b(\d{6})\b', address)
            search_value = postal_match.group(1) if postal_match else address

            # Geocode
            geo_response = requests.get(
                "https://www.onemap.gov.sg/api/common/elastic/search",
                params={
                    "searchVal": search_value,
                    "returnGeom": "Y",
                    "getAddrDetails": "Y",
                    "pageNum": 1
                },
                timeout=10
            )

            geo_data = geo_response.json()
            results = geo_data.get("results", [])
            if not results:
                return None

            lat = results[0]["LATITUDE"]
            lon = results[0]["LONGITUDE"]

            # Get planning area
            pa_response = requests.get(
                "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea",
                params={"latitude": lat, "longitude": lon},
                headers={"Authorization": self.token},
                timeout=10
            )

            pa_data = pa_response.json()
            if pa_data and isinstance(pa_data, list) and pa_data[0].get("pln_area_n"):
                return pa_data[0]["pln_area_n"]

        except Exception as e:
            logger.error(f"Planning area extraction error: {e}")

        return None


def run_scheme_processing_pipeline(doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run pipeline steps 1-4 for a single scheme entry.

    Args:
        doc_id: Firestore document ID from schemeEntries
        data: Document data containing Link, Scheme name, etc.

    Returns:
        Dict with scraped_text, llm_fields, planning_area, logo_url, and original_data
    """
    logger.info(f"Starting pipeline for doc_id: {doc_id}")
    logger.info(f"Emulator mode: {is_emulator_mode()}")

    # Get scheme URL from submission data
    link = data.get("Link") or data.get("link")
    scheme_name = data.get("Scheme") or data.get("scheme_name", "Unknown Scheme")

    result = {
        "doc_id": doc_id,
        "scheme_name": scheme_name,
        "scheme_url": link,
        "scraped_text": None,
        "llm_fields": {},
        "planning_area": None,
        "logo_url": None,
        "original_data": data,
        "processing_status": "pending",
        "error": None,
    }

    if not link:
        result["error"] = "No URL provided in submission"
        result["processing_status"] = "failed"
        logger.error(f"No URL for doc_id {doc_id}")
        return result

    # Step 1 & 2: Crawl and extract using crawl4ai
    try:
        processor = Crawl4AIProcessor()
        scraped_text, llm_fields, logo_url = asyncio.run(processor.process_url(link))
        result["scraped_text"] = scraped_text
        result["llm_fields"] = llm_fields
        result["logo_url"] = logo_url
    except Exception as e:
        logger.error(f"Crawl4ai processing failed for doc_id {doc_id}: {e}")
        result["error"] = f"Processing Error: {str(e)}"
        result["processing_status"] = "failed"
        return result

    # Check for crawling errors
    if scraped_text and scraped_text.startswith(("Crawl Error:", "PDF Processing Error:")):
        result["error"] = scraped_text
        result["processing_status"] = "scraping_failed"
        logger.error(f"Crawling failed for doc_id {doc_id}: {scraped_text}")
        return result

    # Step 3: Extract contact info using regex (more reliable for emails/phones)
    if scraped_text:
        regex_contacts = extract_contact_info_regex(scraped_text)
        logger.info(f"Regex extracted - emails: {regex_contacts['emails']}, phones: {regex_contacts['phones']}")

        # Merge: Prefer regex results for emails/phones (more reliable)
        if regex_contacts['emails']:
            result["llm_fields"]["email"] = ", ".join(regex_contacts['emails'])
        if regex_contacts['phones']:
            result["llm_fields"]["phone"] = ", ".join(regex_contacts['phones'])

    # Step 4: Extract planning area from address
    address = result["llm_fields"].get("address")
    if address:
        try:
            planning_extractor = PlanningAreaExtractor()
            # Handle comma-separated addresses
            if "," in address:
                first_address = address.split(",")[0].strip()
                result["planning_area"] = planning_extractor.extract_planning_area(first_address) or "No Location"
            else:
                result["planning_area"] = planning_extractor.extract_planning_area(address) or "No Location"
        except Exception as e:
            logger.error(f"Planning area extraction failed for doc_id {doc_id}: {e}")
            result["planning_area"] = "No Location"
    else:
        result["planning_area"] = "No Location"

    result["processing_status"] = "completed"
    logger.info(f"Pipeline completed for doc_id: {doc_id}")

    return result
