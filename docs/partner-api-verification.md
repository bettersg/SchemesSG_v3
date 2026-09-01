# Partner API — verification record

Proof of work for the partner API branch (`feat/partner-api-access`). Everything
below was executed, not asserted. Commands are runnable from a clean checkout.

## Status summary

| Gate | Result |
| --- | --- |
| Backend unit + integration tests | **310 passed**, 0 failed |
| `partner/routing.py` coverage | **100%** |
| `partner/serializers.py` coverage | **100%** |
| `partner/search.py` coverage | **100%** |
| `utils/partner_auth.py` coverage | **100%** |
| `partner/api.py` coverage | 65% (remainder is the HTTPS entrypoint and response plumbing) |
| `schemes/catalog.py` coverage | 94% |
| Frontend typecheck (`tsc --noEmit`) | clean |
| Frontend production build | clean, 3 new routes prerendered static |
| Frontend lint | 0 findings in new files (29 pre-existing warnings unchanged) |
| Ruff on changed backend files | clean |
| Adversarial code review (45 agents, 7 dimensions) | 19 raised → 4 confirmed → **all 4 fixed** |
| Docker compose smoke | **NOT RUN** — see "Not verified" below |

## Backend tests

```bash
cd backend && uv run pytest
```

```
310 passed, 1 warning in 10.55s

functions/partner/api.py            97   34   65%
functions/partner/routing.py        36    0  100%
functions/partner/search.py         26    0  100%
functions/partner/serializers.py     8    0  100%
functions/utils/partner_auth.py     37    0  100%
functions/schemes/catalog.py       135    8   94%
```

Baseline before this branch was 278 tests; the branch adds 32.

## The shared-helper change is behaviour-preserving for `/catalog`

`schemes/catalog.py` is shared with the frontend catalog, so the partner list
needed to hide `inactive` without changing what `/catalog` shows.
`_get_listed_paginated_results` now takes `exclude_statuses`, defaulting to
`frozenset({retired})` — exactly what `/catalog` hid before.

The pre-existing test that pins the old behaviour still passes unmodified:

```python
# tests/unit/test_scheme_retirement.py::test_catalog_filters_retired_schemes
assert [item["scheme_id"] for item in result.data] == ["legacy", "active", "inactive"]
#                                                                        ^ still kept for /catalog
```

## Lazy-import boundary

`partner/api.py` keeps the embeddings stack out of its own import graph:

```bash
cd backend/functions && uv run python -c "
import partner.api, sys
print([m for m in ('search.retriever','torch','sentence_transformers','faiss') if m in sys.modules] or 'NONE')"
```

```
NONE
```

**Honest caveat, measured:** this does not make a real cold start cheaper today.
`main.py` imports `agent.handler` at module scope, which reaches
`search.retriever` through `agent/engine.py → router.py → tools/search.py`:

```bash
cd backend/functions && uv run python -c "
import main, sys
print([m for m in ('search.retriever','torch') if m in sys.modules])"
```

```
['search.retriever']
```

Since Firebase loads one `main.py` per deployment, every function already pays
that import. The lazy import is the half this branch controls, and it is guarded
by a test so nothing hoists a search import into the partner path. Making the win
real means deferring `agent.handler`'s import — a separate change to an existing
endpoint, deliberately not in this PR.

## Frontend

```bash
cd frontend && npx tsc --noEmit && npm run build && npm run lint
```

```
✓ Compiled successfully in 3.4s
├ ○ /developers
├ ○ /privacy
└ ○ /terms
```

`○` = prerendered static. Lint reports 0 findings in the new files; the 29
warnings are pre-existing and unchanged from `origin/stg`.

### Rendering, verified in a real browser

Screenshots captured over CDP against the dev server, not asserted from markup:

| Shot | What it shows |
| --- | --- |
| [`01-developers-desktop.jpg`](evidence/partner-api/01-developers-desktop.jpg) | Full `/developers` page at 1440px — all 11 sections, pinned sidebar, dark code panels |
| [`02-privacy-full.jpg`](evidence/partner-api/02-privacy-full.jpg) | `/privacy` |
| [`03-terms-full.jpg`](evidence/partner-api/03-terms-full.jpg) | `/terms` |
| [`04-developers-mobile.jpg`](evidence/partner-api/04-developers-mobile.jpg) | `/developers` at mobile width, after both layout fixes below |

Console on `/developers`: no errors or warnings from page code.

### Two mobile layout bugs found this way and fixed

Both were invisible to tests, typecheck, lint and the build. Measured in-page:

**1. 16px horizontal overflow.** The sidebar's `<ul>` used the full-bleed
`-mx-4 px-4` trick, but its parent `<nav>` had no horizontal padding (the padding
lives on the sibling content column), so the strip hung 1rem past the viewport:

```
before: viewport 500, docScrollWidth 516, ulBox {left: -16, right: 516}
after:  viewport 500, docScrollWidth 500, ulBox {left: 0,   right: 500}
```

Fixed by moving the padding onto the `<nav>` and matching the negative margin per
breakpoint. Verified flush at base (`-16px` vs `16px`) and `sm` (`-32px` vs
`32px`), and unchanged at `lg` (`mx-0`, column flex, sticky 256px rail).

**2. Section strip collided with the fixed navbar.** The strip rendered at `y=0`,
under the site header, because only the content column carried the top offset:

```
before: stripContentTop 0,  navbarBottom 70   ← overlapping
after:  stripContentTop 70, navbarBottom 70, h1Top 162
```

Fixed so the offset applies exactly once per layout (`pt-nav` on the nav below
`lg`, `lg:pt-nav` on the header at `lg`). Desktop unchanged: `h1Top 110`,
`sidebarHeadingTop 70`, zero overflow.

## Adversarial code review

7 dimensions reviewed in parallel, every finding then attacked by 2 independent
verifiers instructed to refute it and to default to "refuted" when uncertain.

```
19 raw findings → 4 confirmed, 15 refuted   (45 agents, 0 errors)
```

All 4 confirmed findings are fixed in this branch:

| Severity | Finding | Fix |
| --- | --- | --- |
| blocker | `POST /v1/schemes/search` returned `500 internal_error` for any valid-JSON body that wasn't an object (`["a"]`, `"hi"`, `5`) — `body.get()` raised `AttributeError` | Validate the body is an object, before the lazy import, so a bad body is a `400 invalid_request` and costs no embeddings load |
| major | List route filtered `inactive` *after* pagination → short pages and a `total_count` counting schemes the API never returns | Pass `exclude_statuses` into the shared helper so the refill loop and count both honour it |
| major | Smoke script's own 8/min budget was spent before the DETAIL and SEARCH checks, so it reported failures against a correct API | Functional key gets headroom; throttling proved on a separate key under its own consumer |
| major | No test covered `_handle_list`, which is how the pagination bug shipped | Added refill, `total_count`, and param-validation tests |

The review also confirmed the fix matches repo convention: the sibling
`schemes/search.py:60-75` already wraps the same `body.get(...)` calls and
returns 400, so the 500 was a regression against existing practice.

Additional hardening applied while in the area (these findings were *refuted* as
unreachable through supported operations — kept anyway because they fail open at
a revocation gate, and the runbook tells operators to hand-edit these fields):

- Only a real boolean `true` authenticates. A hand-typed `"false"` is truthy and
  would previously have kept a revoked key working.
- `rate_limit_per_min: 0` is honoured instead of collapsing to the 60/min default
  via `or`. Documented in the runbook as the pause-without-revoking control.
- A non-numeric `rate_limit_per_min` falls back to the default instead of raising
  a 500 on every request.
- Auth and rate-limiting are wrapped, so a Firestore blip answers in the
  documented error envelope rather than a bare 500.

## Not verified

**The docker compose smoke test has not been run.** The Docker daemon on this
machine stopped responding — the build stalled at "load local bake definitions"
and both `docker version` and `docker ps` hung indefinitely. Nothing about the
branch was implicated; the daemon was already wedged.

This is the one gate that exercises the API over real HTTP against Firestore, so
it is the last thing to run before merge:

```bash
cd backend && docker compose -f docker-compose-firebase.yml up --build
# then, in another shell:
cd backend/functions && uv run python scripts/smoke_partner_api.py --json ../../.evidence/smoke.json
```

It checks every operation and every documented failure mode, asserts no internal
field appears in any payload, asserts the response fields are exactly the
allowlist, and confirms the 429 carries `Retry-After`. It refuses to run outside
the dev project unless `--allow-project` names the target.
