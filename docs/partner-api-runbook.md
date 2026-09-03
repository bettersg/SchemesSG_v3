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
That is the intended long-term base too, not a placeholder — see
[below](#why-we-stay-on-cloudfunctionsnet-and-do-not-use-apischemessg). If it ever
changes, only `PARTNER_API_BASE` in `frontend/src/lib/partner-api-reference.ts`
moves, and partners change one constant.

### Why we stay on cloudfunctions.net, and do not use api.schemes.sg

Short version: **the ugly URL is the most reliable option available.** Every
prettier alternative is worse in a specific, documented way. This was investigated
properly because two earlier arguments for a subdomain turned out to be wrong.

**There is no path collision with the website.** `frontend/firebase.json` rewrites
`/schemes/**` to the Next SSR function, but partner paths are `/partner_api/v1/…`,
which that pattern does not match. Serving under `schemes.sg` would not clash with
the scheme detail pages. (An earlier note in this repo claimed otherwise.)

**CDN caching is also not the problem.** Firebase Hosting sets dynamic content to
`Cache-Control: private` by default, so function responses are not CDN-cached.
(A second earlier claim, also overstated.)

The real reasons, evidenced:

| Option | Why not |
|---|---|
| **Firebase Hosting rewrite** | Hosting rewrites **drop request headers**, and this API authenticates on one. The `Range` header loss is a [Firebase-confirmed, escalated bug](https://stackoverflow.com/questions/70529601/how-to-preserve-headers-in-firebase-hosting-rewrites), and `Authorization` loss through Hosting → Cloud Run is [reported as intermittent](https://stackoverflow.com/questions/79570641/firebase-hosting-rewrites-to-gcp-cloud-run-but-lost-header-authorization) and unresolved. There is no documented header allowlist. Intermittently dropped `X-API-Key` means partners get random `401`s that look like our fault and cannot be reproduced. Also note an apex→www redirect strips headers by itself. |
| **Cloud Run domain mapping** | Supported in `asia-southeast1`, but Google's own docs say it plainly: *"Due to latency issues, they are not production-ready and are not supported at General Availability. At the moment, this option is not recommended for production services."* Cannot disable TLS 1.0/1.1, cannot map to a path, no custom certificates. |
| **Global external ALB + serverless NEG** | Works, and is Google's recommended option — but ~US$18/mo for the forwarding rule plus ~6 networking resources living outside version control, bought purely for a nicer hostname. No WAF, CDN or multi-backend need here to justify it. |

What we have instead: `cloudfunctions.net` is already a distinct origin from
`schemes.sg`, has no CDN in front of it, and **provably forwards `X-API-Key`** —
the 30-check smoke suite passes against it on every run.

If the hostname ever needs to be pretty enough to spend money on, the ALB is the
only production-grade path. **Do not route this API through Hosting rewrites**
regardless of how convenient the Firebase console makes it look.

One key covers all three operations, and one rate-limit budget is shared across
them — spending it on `/v1/schemes` also exhausts `/v1/schemes/search`.

## Which environment do partners actually get?

**Production only, for real traffic.** There are two deployments, and both run
`partner_api`, but they serve different purposes:

Both bases follow the one `{base}` pattern above — substitute the project id, and
never paste a full URL into partner-facing material:

| | `<project>` | Who uses it |
|---|---|---|
| **Production** | `schemessg` | The partner's live product. This is the integration that matters. |
| **Development** | `schemessg-v3-dev` | Sandbox during onboarding, and our own smoke tests. |

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
  `401` caused by pointing a dev key at prod. The `/developers` page helps here:
  it prints the base URL of whichever project served it, so
  `schemessg-v3-dev.web.app/developers` documents the dev host and
  `schemes.sg/developers` documents production.
- **The dev deployment carries no availability expectation.** It tracks the `stg`
  branch and can break at any time. Say so, so nobody builds a demo on it.
- The `cloudfunctions.net` host is the long-term base, not a temporary one. Give
  partners that URL with confidence rather than warning them it will move.

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

**The Firestore TTL policy on `partner_rate_limits.expires_at` is enabled** in both
projects — `state: ACTIVE` on `schemessg` and `schemessg-v3-dev`. Counter documents
are reaped automatically 10 minutes after creation; without it they accumulate one
document per partner per active minute forever.

If it ever needs re-applying (new project, or someone disables it):

```bash
gcloud firestore fields ttls update expires_at \
  --collection-group=partner_rate_limits --project=<project> --enable-ttl
gcloud firestore fields ttls list \
  --collection-group=partner_rate_limits --project=<project>   # expect state: ACTIVE
```

Expect it to take several minutes — the command starts a Firestore field-index
operation and polls until it completes. It is not hung.

## Monitoring

A log-based metric and alert policy exist on production:

| Resource | Name |
|---|---|
| Log-based metric | `partner_api_5xx` — counts `httpRequest.status>=500` on the `partner_api` service |
| Alert policy | `partner_api 5xx rate` — fires on count `> 0` over 5 minutes, auto-closes after 7 days |

**Open item: the alert has no notification channel, so it is currently silent.**
It records incidents in the Monitoring console but sends nothing, because the
project has no notification channels at all. Until one is attached, someone has to
go and look.

To finish it, create a channel (Slack incoming-webhook, or an email alias — email
requires the recipient to click a verification link) and attach it to the policy:

```bash
# list channels; attach one to projects/schemessg/alertPolicies/4380231572188813607
gcloud beta monitoring channels list --project=schemessg
```

This matters more than it looks: the `schemes_search` warmup job failed every four
minutes for months with nothing watching it, which is how #410 stayed invisible. A partner-facing outage failing the
same silent way is the same mistake with a partner relationship attached — and a
policy with no channel is still that mistake, just better documented.

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
deletes the keys it created. Pipe it through `tee` if you want the run on disk.

## Cold starts: not warmed, deliberately

`partner_api` is **not** in `keep_endpoints_warm`, and has no `is_warmup` bypass.
A cold start loads the embeddings stack into a 2GB instance, so the first partner
request after an idle period can wait tens of seconds.

That is accepted. Warmup exists to spare *interactive site users* a cold start; a
server-to-server partner integration is latency-tolerant. Warming this endpoint
would mean standing a live partner key up in function environment configuration,
plus an environment variable whose absence fails silently forever — real
operational surface, to save a wait nobody is sitting in front of.

If a partner ever does report cold starts as a problem, the fix to reach for first
is `minInstances` on this one function, which costs no new credential.

## Deliberate omissions

- **No CORS headers**, and partner domains must never be added to
  `ALLOWED_ORIGINS`. See [the CORS section](#cors-why-there-is-none-and-why-that-is-correct)
  for why this is the security control rather than a gap.
- **No key expiry.** Keys live until revoked. Worth revisiting as the partner
  count grows.
- No SLA, status page, OpenAPI spec, ETags or deprecation policy yet. All real
  concerns for a mature public API; none proportionate to the current partner
  count.
