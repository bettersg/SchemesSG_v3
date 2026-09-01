# Partner API runbook

Operational procedures for the partner API (`partner_api`). The request/response
**contract** lives on [`/developers`](https://schemes.sg/developers) and is not
duplicated here — this document covers issuing, rotating and revoking access.

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

## Onboarding a partner

### 1. Confirm the legal gate — do not skip

Confirm the Terms of Use and Privacy Policy cover **this named consumer** and
state that scheme data is shared with third-party partners via API.

**Do not issue a key before this is true.** Building and testing the mechanism
does not require it; issuing a key to a real consumer does.

### 2. Issue a sandbox key first

```bash
cd backend/functions
uv run python scripts/issue_partner_key.py --dev issue --consumer <name> --rate-limit 60
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
uv run python scripts/issue_partner_key.py --prod issue --consumer <name> --rate-limit 60
```

The script requires you to type the project ID to confirm before it writes to
production.

## Revoking access

```bash
cd backend/functions
uv run python scripts/issue_partner_key.py --prod revoke --consumer <name>
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
uv run python scripts/issue_partner_key.py --dev  list
uv run python scripts/issue_partner_key.py --prod list
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
uv run python scripts/smoke_partner_api.py
```

`scripts/smoke_partner_api.py` writes a temporary `smoke-test` key to whichever
Firestore the emulator is pointed at (by default the `schemessg-v3-dev` cloud
project, since `FIRESTORE_EMULATOR_HOST` is commented out in
`docker-compose-firebase.yml` — vector search needs real Firestore), exercises
every operation and every documented error case, prints a pass/fail table, and
deletes the key it created. Use `--keep-key` to leave it in place for manual
poking, and `--json` to write a machine-readable report.

## Deliberate omissions

- **`partner_api` is not in `keep_endpoints_warm`, and has no `is_warmup` bypass.**
  Warmup spares interactive site users a cold start; a partner server is
  latency-tolerant. A bypass would add an unauthenticated, publicly reachable
  code path to save a cold start nobody waits on. Do not "fix" this.
- **No CORS headers.** `ALLOWED_ORIGINS` is a browser-`Origin` allowlist. A
  partner server sends no `Origin`. **Do not add partner domains to it** — that
  list is for browsers and widening it gates nothing.
- No SLA, status page, OpenAPI spec, ETags or deprecation policy yet. All real
  concerns for a mature public API; none proportionate to the current partner
  count.
