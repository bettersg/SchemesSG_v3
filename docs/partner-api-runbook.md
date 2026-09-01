# Partner API runbook

Operational procedures for the partner API (`partner_api`). The request/response
**contract** lives on [`/developers`](https://schemes.sg/developers) and is not
duplicated here — this document covers issuing, rotating and revoking access.

For *who does what and in what order* — how a partner authenticates, who mints
the key, what they receive and what they deliberately don't get — see
[`partner-api-access-flow.md`](partner-api-access-flow.md).

## What a partner gets

One API key, granting three read operations against a versioned path:

```
GET   {base}/v1/schemes              list + filter
GET   {base}/v1/schemes/{scheme_id}  detail
POST  {base}/v1/schemes/search       semantic search
```

`{base}` is currently `https://asia-southeast1-<project>.cloudfunctions.net/partner_api`.
If a custom domain is later pointed at the function, `{base}` becomes
`https://api.schemes.sg` and partner URLs read `https://api.schemes.sg/v1/schemes`
with no change on the partner's side beyond the base URL.

One key covers all three operations, and one rate-limit budget is shared across
them — spending it on `/v1/schemes` also exhausts `/v1/schemes/search`.

## Which environment do partners actually get?

**Production only, for real traffic.** There are two deployments, and both run
`partner_api`, but they serve different purposes:

| | Project | Base URL | Who uses it |
|---|---|---|---|
| **Production** | `schemessg` | `https://asia-southeast1-schemessg.cloudfunctions.net/partner_api` | The partner's live product. This is the integration that matters. |
| **Development** | `schemessg-v3-dev` | `https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/partner_api` | Sandbox during onboarding, and our own smoke tests. |

A partner is given **two keys over the course of onboarding**, not one: a sandbox
key on dev to build and test against, then a production key once that works. The
keys are not interchangeable — a key issued with `--dev` exists only in the dev
project's `partner_keys` collection, so presenting it to production returns
`401 invalid_key`, and vice versa. That separation is the point: a partner
experimenting cannot touch production data or production rate-limit budget.

Practical consequences:

- **Dev data is not production data.** Scheme ids differ between projects, so a
  partner must not hardcode ids discovered in sandbox.
- **Tell them which base URL goes with which key**, or they will burn a day on a
  `401` caused by pointing a dev key at prod.
- **The dev deployment carries no availability expectation.** It tracks the `stg`
  branch and can break at any time. Say so, so nobody builds a demo on it.
- Long term the production base becomes `https://api.schemes.sg`; only the base
  URL changes for the partner.

## CORS: why there is none, and why that is correct

This comes up every time, so: **CORS is a browser mechanism, not a server-side
access control.** The browser reads `Access-Control-Allow-Origin` and decides
whether to let *its own* JavaScript read the response. A partner's backend —
Python, Node, Go, curl — never consults it. So a server-to-server API needs no
CORS headers to function, and adding them would grant nothing to the intended
client.

Omitting them is itself the security control. The only way a partner could call
this API from browser JavaScript is by shipping their secret key to the browser,
where every end user (and every browser extension) can read it. One leaked key
means unrestricted read access under that partner's identity until we notice and
revoke. Because the headers are absent, that mistake fails in development — the
partner's browser blocks the response and their engineer asks us why — rather
than silently shipping to production.

**So: do not add partner domains to `ALLOWED_ORIGINS`.** That list exists for
`schemes.sg`'s own frontend, which authenticates with short-lived anonymous
Firebase tokens, not with a long-lived secret. Widening it would not make the
partner API "work in the browser" in any safe sense; it would just remove the
guardrail that stops a partner exposing their key.

If a partner genuinely needs scheme data in their frontend, the correct pattern is
the standard one for any secret-key API — Stripe, Twilio and every payments API
work this way:

1. Their browser calls **their own** backend.
2. Their backend calls us, holding the key server-side.
3. Their backend returns whatever subset their UI needs.

That also lets them cache, and keeps their key out of our incident reports. If
first-party browser access ever becomes a real requirement, the answer is a
separate mechanism designed for it — an origin-scoped public key, or short-lived
tokens minted by their backend — not CORS headers bolted onto a secret-key
endpoint.

## Command reference

Every command is `uv run python -m scripts.issue_partner_key <env> <subcommand>`,
run from `backend/functions`. Run it as a module (`-m scripts.…`), not as a file
path — a bare script does not get `functions/` on `sys.path` and dies on imports.

### Choosing the environment: `--dev` / `--prod`

Exactly one is required; there is no default, so you cannot mint a production key
by forgetting a flag.

| Flag | Project | Reads credentials from |
|---|---|---|
| `--dev` | `schemessg-v3-dev` | `backend/functions/.env.dev` |
| `--prod` | `schemessg` | `backend/functions/.env.prod` |

**Gotcha:** these are `.env.dev` / `.env.prod`, *not* the `.env` the emulator and
smoke script use. If you only have `.env` locally the command exits immediately
with `Env file not found: …/.env.dev`. Copy your service-account values into the
matching file first. Each needs `FB_PROJECT_ID`, `FB_CLIENT_EMAIL`,
`FB_PRIVATE_KEY` and the other `FB_*` keys.

`--prod` additionally makes you type the project id at a prompt before it writes.

### `issue` — mint a key

```bash
uv run python -m scripts.issue_partner_key --dev issue --consumer carecompass
```

| Argument | Required | Meaning |
|---|---|---|
| `--consumer` | yes | The partner's identifier, e.g. `carecompass`. Stored on the key document, written into every log line, and used as the rate-limit bucket key. Use one stable lowercase slug per organisation. |
| `--rate-limit` | no (default `600`) | **Requests per minute**, shared across all three operations. Written to the document as `rate_limit_per_min`. |

So `--rate-limit 600` would mean *600 requests per minute* — but 600 is the
default, so you normally omit the flag entirely. Pass it only to deviate.

Two consequences of `--consumer` being the bucket key: reusing an existing
consumer name issues a **second, additional key** that shares that consumer's one
budget (this is how rotation works), and `revoke` acts on the consumer, not on a
single key.

Output is the plaintext key, printed once:

```
  Key:        sk_schemes_<43-char-url-safe-random-string>
  Consumer:   carecompass
  Rate limit: 600 requests/minute
```

Copy it now. Only `sha256(key)` is stored, so nothing can recover it later.

### `list` — audit what exists

```bash
uv run python -m scripts.issue_partner_key --prod list
```

Prints consumer, active flag, rate limit, creation time and a hash prefix — one
row per key, so a consumer mid-rotation shows two. Never prints a usable key.

### `revoke` — turn a partner off

```bash
uv run python -m scripts.issue_partner_key --prod revoke --consumer carecompass
```

Revokes **every key belonging to that consumer**, setting `active: false` and
stamping `revoked_at`. There is no way to revoke one key of a pair from the CLI;
during a rotation overlap, retire the old key by deleting or editing its document
in the console instead.

## What the rate limit actually does

`rate_limit_per_min` is enforced per consumer, per **calendar** minute. Each
request increments `partner_rate_limits/<consumer>:<YYYYMMDDHHMM>` and is allowed
while `count <= rate_limit_per_min`; past that it is `429 rate_limited` with
`Retry-After: 60`. Every response carries `X-RateLimit-Limit` and
`X-RateLimit-Remaining`.

Four things that surprise people:

- **One budget covers all three operations.** Spending it on `/v1/schemes` also
  exhausts `/v1/schemes/search`. It is a per-partner budget, not per-endpoint.
- **Failed requests still cost budget.** The counter increments before routing, so
  a partner hammering a wrong URL or sending bad JSON throttles itself on 404s and
  400s. Only requests rejected at auth (`401`/`403`) cost nothing, because auth
  runs first.
- **The window is fixed, not sliding.** It resets at each `:00`, so a partner can
  legitimately send up to `2 × limit` across a boundary — 600/min allows 1200 in a
  single straddling 60-second span. Fine at current partner counts; size limits
  with that headroom in mind.
- **`0` is a valid limit and means "blocked".** See
  [pausing without revoking](#pausing-without-revoking).

### Choosing a number

**This is not an abuse control.** Partners are hand-vetted and every key is minted
by a maintainer, so the limit exists to bound a *mistake* — a retry loop or a
runaway cron on the partner's side quietly running up Firestore reads and 2GB
function instances. Set it generously and treat a 429 as a bug signal, not as a
partner behaving badly.

600/min (10 req/s) is the default: comfortable for a partner page that fans out
several scheme lookups per view, while still catching a runaway well before it
becomes an invoice.

| Value | Suits |
|---|---|
| `600` | Default. Interactive use from a partner's product, including multi-lookup pages. |
| `1200`–`3000` | A partner doing bulk sync or backfilling their own copy of the catalogue, or one with genuinely high traffic. |
| `60`–`120` | A sandbox key while they build, where a tight limit surfaces accidental loops early. |
| `0` | Blocked. Key stays valid, every request 429s. |

Raise it whenever a trusted partner asks — it needs no re-issue and no redeploy.
Edit `rate_limit_per_min` on their `partner_keys` document and it applies on their
next request.

One asymmetry to keep in mind when going much higher: **search is far more
expensive to serve than list or detail**, because it loads the embeddings and
ranking stack, and both draw on the same budget. A partner cleared for 3000/min of
list traffic is also cleared for 3000/min of search. If that ever matters, split
the budget per operation class rather than lowering the limit for everything.

## Onboarding a partner

### 1. Confirm the legal gate — do not skip

Confirm the Terms of Use and Privacy Policy cover **this named consumer** and
state that scheme data is shared with third-party partners via API.

**Do not issue a key before this is true.** Building and testing the mechanism
does not require it; issuing a key to a real consumer does.

### 2. Issue a sandbox key first

```bash
cd backend/functions
uv run python -m scripts.issue_partner_key --dev issue --consumer <name>
```

This writes a `partner_keys` document to `schemessg-v3-dev`, keyed by
`sha256(key)`, and prints the plaintext key **once**. It is not stored and cannot
be recovered — if it is lost, revoke and re-issue.

Let the partner integrate and verify against sandbox data before production is
involved at all.

### 3. Hand the key over out-of-band

Not plaintext email, not Slack — anywhere it lingers in a searchable archive.
Use whatever channel the partnership owner already uses for credentials.

### 4. Point them at the docs

Send them to `/developers`. It documents auth, the base URL, all three
operations, the field reference, error codes and rate-limit headers. Don't
paste request shapes into email; they go stale.

### 5. Issue the production key

Only once sandbox is verified:

```bash
uv run python -m scripts.issue_partner_key --prod issue --consumer <name>
```

The script requires you to type the project ID to confirm before it writes to
production.

## Revoking access

```bash
cd backend/functions
uv run python -m scripts.issue_partner_key --prod revoke --consumer <name>
```

Or flip `active: false` on the `partner_keys` document in the Firestore console.
Only a real boolean `true` authenticates, so a hand-typed `"false"` string fails
closed rather than leaving the key working.

Either way it takes effect on the **next request** — no redeploy, and it never
touches the Firebase Auth users that every anonymous browser session depends on.

### Pausing without revoking

To stop a partner's traffic while keeping the key valid, set
`rate_limit_per_min: 0` on their document. Every request then returns
`429 rate_limited` until you restore a real limit. Prefer `revoke` for anything
permanent — it stamps `revoked_at` and returns a clearer `403` to the partner.

## Auditing issued keys

```bash
uv run python -m scripts.issue_partner_key --dev  list
uv run python -m scripts.issue_partner_key --prod list
```

Lists consumer, active flag, rate limit, creation time and a hash prefix.
Plaintext keys are deliberately unrecoverable.

## Rotating a key

There is no in-place rotation. Issue a new key, have the partner cut over, then
revoke the old one. Both keys work during the overlap, and they share one budget
per consumer.

## Firestore collections

| Collection | Purpose | Notes |
|---|---|---|
| `partner_keys` | Document ID is `sha256(key)`. Fields: `consumer`, `active`, `created_at`, `rate_limit_per_min`. | Raw keys are never stored. |
| `partner_rate_limits` | Document ID is `<consumer>:<YYYYMMDDHHMM>`. Fields: `count`, `consumer`, `expires_at`. | One doc per partner per minute. |

**Set a Firestore TTL policy on `partner_rate_limits.expires_at`** so counter
documents are reaped automatically. Without it they accumulate one document per
partner per active minute. This is a console/infra step, not code.

## Monitoring

Set a log-based alert on the `partner_api` 5xx rate.

This is not optional bookkeeping: the `schemes_search` warmup job has been
failing every four minutes with nothing watching it. A partner-facing outage
failing the same silent way is the same mistake with a partner relationship
attached.

## Local verification

The emulator serves the function at the same paths:

```bash
cd backend
docker compose -f docker-compose-firebase.yml up --build

# In a second shell: seed a key, exercise every operation and failure mode
cd backend/functions
uv run python -m scripts.smoke_partner_api
```

`scripts/smoke_partner_api.py` writes a temporary `smoke-test` key to whichever
Firestore the emulator is pointed at (by default the `schemessg-v3-dev` cloud
project, since `FIRESTORE_EMULATOR_HOST` is commented out in
`docker-compose-firebase.yml` — vector search needs real Firestore), exercises
every operation and every documented error case, prints a pass/fail table, and
deletes the key it created. Use `--keep-key` to leave it in place for manual
poking, and `--json` to write a machine-readable report.

## Keeping it warm

`partner_api` is warmed by `keep_endpoints_warm` alongside the rest of the API,
every 4 minutes. This matters more here than elsewhere: a cold start loads the
embeddings stack into a 2GB instance, so an unwarmed partner request can wait tens
of seconds.

The warmer authenticates like any other caller. Every other endpoint accepts the
Firebase ID token `make_warmup_request` mints; `partner_api` does not, so it needs
a real API key. The `is_warmup` short-circuit sits **after** key verification and
**before** the rate limiter — so it is not an unauthenticated path, and the ping
neither spends a partner's budget nor writes a counter document.

### One-time setup per project

```bash
cd backend/functions
uv run python -m scripts.issue_partner_key --prod issue --consumer warmup --rate-limit 0
```

Then set the printed key as `PARTNER_WARMUP_API_KEY` in that project's function
environment. Repeat with `--dev` for the dev project.

`--rate-limit 0` is deliberate and safe here: the warmup path returns before the
rate limiter runs, so a zero budget never blocks it, while ensuring the key is
useless for fetching data if it ever leaks. Verify with:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  "$BASE/v1/schemes?limit=1" -H "X-API-Key: $PARTNER_WARMUP_API_KEY"   # expect 429
curl -s "$BASE/v1/schemes?is_warmup=true" -H "X-API-Key: $PARTNER_WARMUP_API_KEY"  # expect 200
```

If `PARTNER_WARMUP_API_KEY` is unset, `keep_endpoints_warm` logs a warning and
skips `partner_api` rather than failing the whole warmup run.

## Deliberate omissions

- **No CORS headers**, and partner domains must never be added to
  `ALLOWED_ORIGINS`. See [the CORS section](#cors-why-there-is-none-and-why-that-is-correct)
  for why this is the security control rather than a gap.
- **No key expiry.** Keys live until revoked. Worth revisiting as the partner
  count grows.
- No SLA, status page, OpenAPI spec, ETags or deprecation policy yet. All real
  concerns for a mature public API; none proportionate to the current partner
  count.
