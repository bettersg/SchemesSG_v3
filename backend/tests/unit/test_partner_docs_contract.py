"""Guards the published /developers page against the backend it documents.

`frontend/src/lib/partner-api-reference.ts` restates the field allowlist, the error
codes, the header name and the default rate limit. That duplication is unavoidable
across a Python/TypeScript boundary, but without a check nothing fails when the two
drift — the partner-facing docs would simply start lying.

Parsed with a regex rather than a TS toolchain on purpose: pytest already runs in
CI, and the alternative is standing up node inside the backend test suite to read
four literals.
"""

import re
from pathlib import Path

import pytest
from new_scheme.constants import SCHEME_CATEGORY_MAPPING
from partner.serializers import PUBLIC_FIELDS
from utils.partner_auth import API_KEY_HEADER, DEFAULT_RATE_LIMIT_PER_MIN


REFERENCE_TS = (
    Path(__file__).resolve().parents[2].parent
    / "frontend"
    / "src"
    / "lib"
    / "partner-api-reference.ts"
)

# Error codes the backend can actually return, and where each is raised.
BACKEND_ERROR_CODES = {
    "missing_key",
    "invalid_key",
    "revoked_key",
    "rate_limited",
    "unsupported_version",
    "not_found",
    "method_not_allowed",
    "invalid_request",
    "scheme_retired",
    "internal_error",
}


@pytest.fixture(scope="module")
def reference_source() -> str:
    if not REFERENCE_TS.exists():
        pytest.skip(f"docs reference not present at {REFERENCE_TS}")
    return REFERENCE_TS.read_text()


def _block(source: str, const_name: str) -> str:
    """Return the source text of one `export const NAME = ...;` declaration."""
    start = source.index(f"export const {const_name}")
    end = source.index("\nexport const", start + 1) if "\nexport const" in source[start + 1 :] else len(source)
    return source[start:end]


def test_documented_scheme_fields_match_the_allowlist(reference_source):
    """Every field on /developers must be one the serializer actually emits."""
    documented = set(re.findall(r'name:\s*"([^"]+)"', _block(reference_source, "SCHEME_FIELDS")))
    assert documented == set(PUBLIC_FIELDS), (
        "The /developers field table has drifted from PUBLIC_FIELDS.\n"
        f"  documented but not served: {sorted(documented - set(PUBLIC_FIELDS))}\n"
        f"  served but undocumented:   {sorted(set(PUBLIC_FIELDS) - documented)}"
    )


def test_documented_categories_match_the_backend_mapping(reference_source):
    """The docs shipped `category=healthcare`, which 400s — nothing tied the two.

    `_expand_category` accepts only these exact names, case-insensitively, so a
    documented value outside the mapping is a copy-pasteable request that fails.
    """
    # Scoped to the array literal, not _block: the next `export const` is far
    # below, past several `export type` declarations that would match too.
    literal = re.search(r"export const CATEGORIES = \[(.*?)\];", reference_source, re.DOTALL)
    assert literal, "CATEGORIES array not found in the reference"
    documented = set(re.findall(r'"([^"]+)"', literal.group(1)))
    assert documented == set(SCHEME_CATEGORY_MAPPING), (
        "The /developers category list has drifted from SCHEME_CATEGORY_MAPPING.\n"
        f"  documented but invalid: {sorted(documented - set(SCHEME_CATEGORY_MAPPING))}\n"
        f"  valid but undocumented: {sorted(set(SCHEME_CATEGORY_MAPPING) - documented)}"
    )


def test_documented_example_requests_use_a_real_category(reference_source):
    """Guards the curl samples, not just the list — the 400 came from a sample."""
    for raw in re.findall(r"[?&]category=([^&\"\s]+)", reference_source):
        value = raw.replace("%20", " ").replace("%26", "&")
        assert value.lower() in {name.lower() for name in SCHEME_CATEGORY_MAPPING}, (
            f"example request uses category={raw!r}, which the backend rejects with 400"
        )


def test_documented_error_codes_are_ones_the_backend_returns(reference_source):
    """A partner coding against a code we never send has no way to find out."""
    documented = set(re.findall(r'code:\s*"([^"]+)"', _block(reference_source, "API_ERRORS")))
    unknown = documented - BACKEND_ERROR_CODES
    assert not unknown, f"/developers documents error codes the backend never returns: {sorted(unknown)}"


def test_documented_api_key_header_matches_the_one_we_read(reference_source):
    documented = re.search(r'API_KEY_HEADER = "([^"]+)"', reference_source)
    assert documented and documented.group(1) == API_KEY_HEADER


def test_documented_default_rate_limit_matches_the_backend(reference_source):
    """The sample 429 body quotes a number; it must be the real default."""
    quoted = re.findall(r"Rate limit of (\d+) requests/minute", reference_source)
    assert quoted, "no sample rate-limit message found in the reference"
    assert {int(value) for value in quoted} == {DEFAULT_RATE_LIMIT_PER_MIN}
