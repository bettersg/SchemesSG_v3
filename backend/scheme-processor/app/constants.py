"""
Domain Constants for Scheme Processing.

Contains category lists, patterns, and prompts used throughout the pipeline.
"""

# =============================================================================
# Categorization Constants
# =============================================================================

WHO_IS_IT_FOR = [
    "Children",
    "Youth",
    "Youth-at-risk",
    "Teenagers facing pregnancy",
    "Young adults",
    "Students",
    "Families",
    "Single parents",
    "Women",
    "Pregnant individuals in distress",
    "Elderly",
    "Elderly with dementia",
    "Persons with disabilities (PWDs)",
    "Persons with special needs",
    "Persons on autism spectrum",
    "Persons with chronic or terminal illnesses",
    "Persons with mental health issues",
    "Caregivers",
    "Low income",
    "Low income families",
    "Low income elderly",
    "Unemployed",
    "Retrenched",
    "Homeless",
    "Need shelter",
    "Need food support",
    "Foreign domestic workers/maids",
    "Migrant workers/Foreign workers",
    "Ex-offenders",
    "Inmates",
    "Families of inmates or ex-offenders",
    "Victims of abuse or harassment",
    "Facing end of life",
    "Facing financial hardship",
    "Need mortgage support",
    "Individuals needing legal aid",
    "Individuals struggling with loss",
    "Individuals with gambling addiction",
    "Transnational families/Foreign spouses",
    "Malay/Muslim community",
    "Indian community",
    "Chinese community",
    "General public",
]

WHAT_IT_GIVES = [
    "Counselling",
    "Casework",
    "Emotional care",
    "Mental health assessment and treatment",
    "Psychological support/Psychotherapy",
    "Befriending services",
    "Helpline services",
    "Referral services",
    "Educational programmes",
    "Vocational training",
    "Employment assistance",
    "Skills training and job matching",
    "Financial assistance (general)",
    "Financial assistance for daily living expenses",
    "Financial assistance for healthcare",
    "Financial assistance for education",
    "Financial assistance for housing",
    "Food support",
    "Housing/Shelter",
    "Respite care/Caregiver support",
    "Child protection services",
    "Childcare services",
    "Transport subsidies",
    "Healthcare (general/basic services)",
    "Dental services",
    "Rehabilitation services",
    "Legal aid and services",
    "Protection against violence",
    "Residential care/programmes",
    "Support groups",
    "Bereavement support",
    "End-of-life care",
    "Technology assistance",
    "Information services",
]

SCHEME_TYPE = [
    "Low Income",
    "Family",
    "Children",
    "Youth",
    "Youth-at-Risk",
    "Women",
    "Single Parents",
    "Elderly",
    "Caregiver Support",
    "Persons with Disabilities (PWD)",
    "Special Needs",
    "Ex-offender Support",
    "Education Support",
    "Healthcare",
    "Mental Health",
    "End-of-Life/Palliative Care",
    "Food Support",
    "Housing/Shelter",
    "Employment Support",
    "Vocational Training",
    "Financial Assistance",
    "Transport Support",
    "Legal Aid",
    "Abuse/Family Violence",
    "COVID-19 Support",
    "Counselling and Emotional Support",
    "General Public Support",
]

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
