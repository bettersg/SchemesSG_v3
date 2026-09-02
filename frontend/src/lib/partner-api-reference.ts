/**
 * Partner API reference data.
 *
 * Identifiers only: paths, field names, types, HTTP codes. These are not
 * translated, because they are literals a partner sends and receives. Narrative
 * copy lives in the landing i18n dictionaries under `developers`.
 *
 * Kept in one module so the base URL appears exactly once. The cloudfunctions.net
 * host is deliberate and long-term, not a placeholder for api.schemes.sg — see
 * docs/partner-api-runbook.md for why every prettier option is worse. If it ever
 * does move, only PARTNER_API_BASE changes.
 *
 * The host follows the project this page was *built* for: production documents
 * production, and the dev deployment documents dev. This replaces a hardcoded
 * production URL, which made the dev page hand out curl commands that 401 against
 * the dev key you were testing with. Baked in at build time, since /developers is
 * statically prerendered.
 */

const PARTNER_API_PROJECT_ID =
  process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "schemessg";

export const PARTNER_API_BASE =
  `https://asia-southeast1-${PARTNER_API_PROJECT_ID}.cloudfunctions.net/partner_api`;

export const PARTNER_API_VERSION = "v1";

export const API_KEY_HEADER = "X-API-Key";

/**
 * Accepted `category` values, mirroring the keys of `SCHEME_CATEGORY_MAPPING` in
 * `backend/functions/new_scheme/constants.py`.
 *
 * The backend matches these case-insensitively but demands the exact name, so a
 * slug does not work. This list previously said "healthcare" and
 * "financial-assistance", neither of which is a category — the documented
 * quick-start request returned 400. `test_partner_docs_contract.py` now pins this
 * array to the backend mapping so the two cannot drift again.
 */
export const CATEGORIES = [
  "Financial Assistance",
  "Family & Children",
  "Health & Wellbeing",
  "Housing & Food",
  "Education",
  "Employment & Training",
  "Seniors & Caregiving",
  "Disability & Transport",
  "Legal & Safety",
  "Community Support",
];

export type HttpMethod = "GET" | "POST";

export type ApiParam = {
  name: string;
  type: string;
  required: boolean;
  description: string;
  example?: string;
};

export type ApiOperation = {
  id: string;
  name: string;
  method: HttpMethod;
  path: string;
  summary: string;
  params: ApiParam[];
  paramsLabel: "query" | "path" | "body";
  request: string;
  response: string;
};

const AUTH_HEADER_LINE = `  -H "${API_KEY_HEADER}: $SCHEMES_API_KEY"`;

export const OPERATIONS: ApiOperation[] = [
  {
    id: "list-schemes",
    name: "List schemes",
    method: "GET",
    path: `/${PARTNER_API_VERSION}/schemes`,
    summary:
      "Page through active schemes. Pass at most one filter at a time. Results exclude retired and inactive schemes.",
    paramsLabel: "query",
    params: [
      {
        name: "category",
        type: "string",
        required: false,
        description:
          `One of: ${CATEGORIES.join(", ")}. Case-insensitive, but the name must match exactly — a slug such as "financial-assistance" is rejected. Cannot be combined with agency or area.`,
        example: "Financial Assistance",
      },
      {
        name: "agency",
        type: "string",
        required: false,
        description:
          "Filter by the agency that runs the scheme. Cannot be combined with category or area.",
        example: "MSF",
      },
      {
        name: "area",
        type: "string",
        required: false,
        description:
          "Filter by planning area. Cannot be combined with category or agency.",
        example: "BEDOK",
      },
      {
        name: "limit",
        type: "integer",
        required: false,
        description: "Schemes per page. Defaults to 10, capped at 50.",
        example: "20",
      },
      {
        name: "cursor",
        type: "string",
        required: false,
        description:
          "Opaque cursor from a previous response's next_cursor. Omit for the first page.",
      },
    ],
    request: `curl "${PARTNER_API_BASE}/${PARTNER_API_VERSION}/schemes?category=Financial%20Assistance&limit=2" \\
${AUTH_HEADER_LINE}`,
    response: `{
  "data": [
    {
      "scheme_id": "0kZ2mQ1xVbN4pR7t",
      "scheme": "ComCare Short-to-Medium-Term Assistance",
      "description": "Monthly cash assistance for households ...",
      "summary": "Monthly cash help while you get back on your feet.",
      "eligibility": "Singapore Citizen or PR, little or no income ...",
      "who_is_it_for": ["Low-income households"],
      "what_it_gives": ["Monthly cash assistance", "Household support"],
      "scheme_type": ["Financial Assistance"],
      "agency": "Ministry Of Social And Family Development",
      "link": "https://www.msf.gov.sg/...",
      "address": "512 Thomson Road",
      "phone": "1800 222 0000",
      "email": "enquiries@msf.gov.sg",
      "service_area": "Nationwide",
      "planning_area": ["BEDOK", "TAMPINES"],
      "image": "https://.../comcare.png",
      "status": "active"
    }
  ],
  "next_cursor": "eyJkb2NfaWQiOiIwa1oy...",
  "has_more": true,
  "total_count": 214
}`,
  },
  {
    id: "retrieve-scheme",
    name: "Retrieve a scheme",
    method: "GET",
    path: `/${PARTNER_API_VERSION}/schemes/{scheme_id}`,
    summary:
      "Fetch one scheme by id. Retired and inactive schemes return 404; a scheme retired by merging into another carries the new id.",
    paramsLabel: "path",
    params: [
      {
        name: "scheme_id",
        type: "string",
        required: true,
        description:
          "The scheme's id, as returned in scheme_id by list or search.",
        example: "0kZ2mQ1xVbN4pR7t",
      },
    ],
    request: `curl "${PARTNER_API_BASE}/${PARTNER_API_VERSION}/schemes/0kZ2mQ1xVbN4pR7t" \\
${AUTH_HEADER_LINE}`,
    response: `{
  "data": {
    "scheme_id": "0kZ2mQ1xVbN4pR7t",
    "scheme": "ComCare Short-to-Medium-Term Assistance",
    "description": "Monthly cash assistance for households ...",
    "eligibility": "Singapore Citizen or PR, little or no income ...",
    "agency": "Ministry Of Social And Family Development",
    "link": "https://www.msf.gov.sg/...",
    "status": "active"
  }
}`,
  },
  {
    id: "search-schemes",
    name: "Search schemes",
    method: "POST",
    path: `/${PARTNER_API_VERSION}/schemes/search`,
    summary:
      "Rank schemes against a natural-language description of someone's situation. Same retrieval the Schemes.sg assistant uses, without the conversational layer.",
    paramsLabel: "body",
    params: [
      {
        name: "query",
        type: "string",
        required: true,
        description:
          "Plain-language description of the situation, not keywords. Longer is better.",
        example: "retired, living alone, struggling with medical bills",
      },
      {
        name: "limit",
        type: "integer",
        required: false,
        description: "Results per page. Defaults to 20, capped at 50.",
        example: "10",
      },
      {
        name: "cursor",
        type: "string",
        required: false,
        description:
          "Opaque cursor from a previous response's next_cursor. Omit for the first page.",
      },
    ],
    request: `curl -X POST "${PARTNER_API_BASE}/${PARTNER_API_VERSION}/schemes/search" \\
${AUTH_HEADER_LINE} \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "retired, living alone, struggling with medical bills",
    "limit": 10
  }'`,
    response: `{
  "data": [
    {
      "scheme_id": "7bQ4rT2yWcM9nL3v",
      "scheme": "MediFund",
      "summary": "Help with hospital bills you still cannot afford.",
      "agency": "Ministry Of Health",
      "scheme_type": ["Health & Wellbeing"],
      "status": "active"
    }
  ],
  "next_cursor": null,
  "has_more": false,
  "total_count": 8
}`,
  },
];

export type SchemeField = {
  name: string;
  type: string;
};

/**
 * The complete response allowlist. Nothing outside this list is ever returned.
 *
 * Types are what the API actually sends, measured against all 704 production
 * schemes — not what the shape ought to be. Five of them were wrong until now:
 * `service_area` was published as an array and is a plain string in every single
 * document, while `planning_area`, `address`, `phone` and `email` vary per
 * document because they were written by different ingestion vintages. A partner
 * generating a typed client from the old list broke on the first page.
 *
 * Keys are always all 17 — `to_public_scheme` fills a missing value with null
 * rather than dropping the key — so only the value types vary.
 */
export const SCHEME_FIELDS: SchemeField[] = [
  { name: "scheme_id", type: "string" },
  { name: "scheme", type: "string" },
  { name: "description", type: "string" },
  { name: "summary", type: "string" },
  { name: "eligibility", type: "string" },
  { name: "who_is_it_for", type: "string[]" },
  { name: "what_it_gives", type: "string[]" },
  { name: "scheme_type", type: "string[]" },
  { name: "agency", type: "string" },
  { name: "link", type: "string" },
  { name: "address", type: "string | string[]" },
  { name: "phone", type: "string | string[]" },
  { name: "email", type: "string | string[]" },
  { name: "service_area", type: "string" },
  { name: "planning_area", type: "string | string[]" },
  { name: "image", type: "string" },
  { name: "status", type: "string" },
];

export type ApiError = {
  status: number;
  code: string;
};

export const API_ERRORS: ApiError[] = [
  { status: 400, code: "invalid_request" },
  { status: 401, code: "missing_key" },
  { status: 401, code: "invalid_key" },
  { status: 403, code: "revoked_key" },
  { status: 404, code: "not_found" },
  { status: 404, code: "scheme_retired" },
  { status: 404, code: "unsupported_version" },
  { status: 405, code: "method_not_allowed" },
  { status: 429, code: "rate_limited" },
  { status: 500, code: "internal_error" },
];

export const ERROR_ENVELOPE = `{
  "error": {
    "code": "rate_limited",
    "message": "Rate limit of 600 requests/minute exceeded"
  }
}`;

export const RETIRED_RESPONSE = `{
  "error": {
    "code": "scheme_retired",
    "message": "Scheme was retired and merged into another scheme",
    "merged_into": "9fH1jK8sZxC5vB2n"
  }
}`;

export const RATE_LIMIT_HEADERS = [
  "X-RateLimit-Limit",
  "X-RateLimit-Remaining",
  "Retry-After",
];
