"""
Domain Constants for Scheme Processing.

Contains category lists, patterns, and prompts used throughout the pipeline.
"""

# =============================================================================
# Categorization Constants
# =============================================================================

# Vocabulary is generated from the canonical taxonomy (scripts/ncss_eval/taxonomy.py -> export_taxonomy.py)
# and vendored as taxonomy_data.json next to this module. Do not edit the lists by hand.
import json
from pathlib import Path

TAXONOMY = json.loads((Path(__file__).parent / "taxonomy_data.json").read_text())
WHO_IS_IT_FOR = [t["name"] for t in TAXONOMY["who_is_it_for"]]
WHAT_IT_GIVES = [t["name"] for t in TAXONOMY["what_it_gives"]]
SCHEME_TYPE = [t["name"] for t in TAXONOMY["scheme_type"]]


# Category -> scheme_type values: a partition of SCHEME_TYPE (each term in exactly one category).
SCHEME_CATEGORY_MAPPING = TAXONOMY["category_mapping"]
# Pre-v2 scheme_type values per category, accepted by category lookups until the data is migrated.
LEGACY_CATEGORY_TERMS = TAXONOMY["legacy_category_mapping"]

# Pre-v2 category lists. Kept only as the seed for the union in taxonomy_data.json (old-vocabulary data until migrated).
LEGACY_SCHEME_CATEGORY_MAPPING = {
    "Financial Assistance": [
        "Financial Assistance",
        "Low Income",
        "COVID-19 Support",
    ],
    "Family & Children": [
        "Family",
        "Children",
        "Youth",
        "Youth-at-Risk",
        "Single Parents",
        "Women",
    ],
    "Health & Wellbeing": [
        "Healthcare",
        "Mental Health",
        "End-of-Life/Palliative Care",
        "Counselling and Emotional Support",
    ],
    "Housing & Food": [
        "Housing/Shelter",
        "Food Support",
    ],
    "Education": [
        "Education Support",
    ],
    "Employment & Training": [
        "Employment Support",
        "Vocational Training",
        "Ex-offender Support",
    ],
    "Seniors & Caregiving": [
        "Elderly",
        "Caregiver Support",
    ],
    "Disability & Transport": [
        "Persons with Disabilities (PWD)",
        "Special Needs",
        "Transport Support",
    ],
    "Legal & Safety": [
        "Legal Aid",
        "Abuse/Family Violence",
    ],
    "Community Support": [
        "General Public Support",
    ],
}

# =============================================================================
# Logo Detection Patterns
# =============================================================================

LOGO_PATTERNS = ["logo", "brand", "icon", "emblem"]

HEADER_PATTERNS = ["header", "nav", "navbar", "footer", "masthead", "top-bar", "topbar"]

NEGATIVE_PATTERNS = [
    "banner",
    "hero",
    "background",
    "social",
    "facebook",
    "twitter",
    "linkedin",
    "instagram",
    "youtube",
    "ad-",
    "promo",
    "slider",
    "carousel",
    "gallery",
    "thumbnail",
    "avatar",
    "profile",
]

# =============================================================================
# Cloudflare/Bot Protection Detection
# =============================================================================

CLOUDFLARE_INDICATORS = [
    "cloudflare",
    "challenge",
    "ray id",
    "cf-browser-verification",
    "just a moment",
    "checking your browser",
    "enable javascript",
]

BOT_PROTECTION_INDICATORS = [
    "err_blocked",
    "cloudflare",
    "captcha",
    "challenge",
    "forbidden",
    "403",
    "bot",
    "blocked_by_client",
]

# =============================================================================
# LLM Extraction Prompt
# =============================================================================

EXTRACTION_INSTRUCTION = """You are an expert extraction algorithm for Singapore social service schemes.
Extract the requested attributes accurately from the given website text.

For who_is_it_for: select ALL applicable values from the allowed options that describe the target audience.
For what_it_gives: select ALL applicable values from the allowed options that describe the benefits/services provided.
For scheme_type: select ALL applicable values from the allowed options that categorize this scheme.

For agency: extract the organization name that provides this scheme/service.
For search_booster: generate relevant keywords that people might use to search for this scheme (comma-separated).

If a value cannot be determined from the content, return null for that field."""
