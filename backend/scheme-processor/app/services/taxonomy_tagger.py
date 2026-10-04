"""Taxonomy tagging: one strict-schema LLM call that assigns who_is_it_for / what_it_gives / scheme_type.

The prompt and schema are the ones measured in the NCSS gate (scripts/ncss_eval/run_luna.py renders the same text from here).
Separate from the multi-field extraction call on purpose: the gate numbers were measured on taxonomy fields alone.
Enum-constrained output means the model cannot return a term outside the vocabulary. Uses the Azure OpenAI SDK
directly (the client the gate measured): litellm does not know the luna deployment and rejects reasoning_effort, and the
extractor's drop_params=True would have dropped it silently.
"""

import json
import os
from typing import Any, Dict, Optional

from app import taxonomy as tx
from loguru import logger

TAGGING_EFFORT = "medium"
MAX_TERMS = {"who_is_it_for": 8, "what_it_gives": 6, "scheme_type": 4}  # age terms are re-derived in code, so who has headroom


def _array(field: str) -> Dict[str, Any]:
    return {"type": "array", "maxItems": MAX_TERMS[field], "items": {"type": "string", "enum": tx.term_names(field)}}


TAGGING_SCHEMA = {
    "name": "ncss_tags",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["who_is_it_for", "what_it_gives", "scheme_type", "age_min", "age_max", "rationale"],
        "properties": {
            "who_is_it_for": _array("who_is_it_for"),
            "what_it_gives": _array("what_it_gives"),
            "scheme_type": _array("scheme_type"),
            "age_min": {"type": ["integer", "null"]},
            "age_max": {"type": ["integer", "null"]},
            "rationale": {"type": "string"},
        },
    },
}


def _defs(field: str) -> str:
    return "\n".join(f"- {t['name']}: {t['definition']}" for t in tx.TAXONOMY[field])


_PROMPT_TEMPLATE = """You tag Singapore social-service schemes using the NCSS-aligned taxonomy below. Select ALL applicable terms per field, only if the text supports them; do not guess.
Rules:
- Mental health conditions are NOT disabilities. Only permanent intellectual/physical disabilities count as "Persons with disabilities (PWDs)".
- Use "General public" only when no other who_is_it_for term fits.
- Age: report the stated age range in age_min/age_max (null if none or open-ended). Age terms are re-derived in code from the range (every overlapping band is tagged), so also select age terms consistent with the range: Infants and toddlers 0-3; Preschool 4-6; Primary 7-12; Children = umbrella 0-12; Teenagers 13-17; Youth = umbrella 13-21; Adults 22-59; Seniors 60+. Select EVERY band the stated range overlaps (e.g. 15-25 => Teenagers, Youth, Adults; 18 and above => Youth, Adults, plus Elderly ONLY if seniors are explicitly targeted). When only a group is named (e.g. 'children') without ages, pick the best-matching terms.
- Precision over recall: tag only what the scheme clearly targets/provides as a main focus. Skip marginal or passing mentions. Most schemes need 2-5 who terms, 2-5 what terms, 1-3 scheme_type terms; hard caps are enforced.
- age_min/age_max: the ages of the people the scheme ultimately SERVES. If a scheme serves parents/caregivers on behalf of children of a stated age (e.g. 'parents of children up to 16'), use the children's ages, because child age groups matter for search. Otherwise participants/beneficiaries only. Ignore ages of volunteers, staff, professionals or eligibility of referrers. If the text says 'N and above', set age_min=N and age_max=null. If it says there is no age restriction or serves all ages, set BOTH to null (never 0/null). Select an age term for 'Seniors' only if the scheme targets seniors (60+) explicitly or age_min >= 60.
- rationale: one or two sentences.

WHO_IS_IT_FOR terms:
{who_is_it_for}

WHAT_IT_GIVES terms:
{what_it_gives}

SCHEME_TYPE terms (needs addressed):
{scheme_type}"""


def build_system_prompt() -> str:
    return _PROMPT_TEMPLATE.format(**{f: _defs(f) for f in tx.FIELDS})


def build_user_text(fields: Dict[str, Any]) -> str:
    """Same shape as the eval's frozen input: name, agency and the descriptive fields only."""
    parts = [f"Scheme: {fields.get('scheme') or ''}", f"Agency: {fields.get('agency') or ''}"]
    desc = (fields.get("description") or "").strip()
    llm = (fields.get("llm_description") or "").strip()
    if desc:
        parts.append(f"Description: {desc[:3500]}")
    if llm and llm != desc:
        parts.append(f"Detailed description: {llm[:3500]}")
    summary = fields.get("summary")
    if summary and str(summary).strip() not in (desc, llm):
        parts.append(f"Summary: {str(summary)[:600]}")
    if fields.get("eligibility"):
        parts.append(f"Eligibility: {str(fields['eligibility'])[:1500]}")
    return "\n".join(parts)


def parse_tagging_response(raw: str) -> Dict[str, Optional[list]]:
    """Validate the model JSON against the vocabulary, apply code-derived age bands, return v2 tags (None when empty)."""
    data = json.loads(raw)
    out: Dict[str, Any] = {}
    for field in tx.FIELDS:
        matched, _ = tx.normalize_terms(field, data.get(field))
        out[field] = matched
    out["who_is_it_for"] = tx.apply_age_terms(out["who_is_it_for"], data.get("age_min"), data.get("age_max"))
    return {f: (v or None) for f, v in out.items()}


def tag_scheme(fields: Dict[str, Any], deployment: Optional[str] = None) -> Dict[str, Optional[list]]:
    """Call the tagging model. Raises on API errors; the caller decides whether to fall back."""
    from openai import AzureOpenAI

    deployment = deployment or os.getenv("AZURE_OPENAI_TAGGING_DEPLOYMENT", "gpt-6-luna")
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_version=os.getenv("OPENAI_API_VERSION", "2025-01-01-preview"),
    )
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "system", "content": build_system_prompt()}, {"role": "user", "content": build_user_text(fields)}],
        response_format={"type": "json_schema", "json_schema": TAGGING_SCHEMA},
        reasoning_effort=TAGGING_EFFORT,
        max_completion_tokens=8000,
    )
    content = response.choices[0].message.content or ""
    if not content:
        logger.error(f"Empty tagging response. Usage: {response.usage}")
        raise ValueError("empty tagging response")
    return parse_tagging_response(content)
