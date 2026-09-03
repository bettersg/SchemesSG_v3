# Backend test suite

Run the canonical secretless suite from `backend/`:

```bash
uv run --frozen pytest
uv run --frozen coverage json -o - | uv run --frozen python scripts/check_coverage.py
```

`pyproject.toml` is the single pytest configuration source. It controls
discovery, import paths, strict marker registration, warning filters, the
default smoke-test exclusion, and branch-aware coverage. The second command
enforces the parent-approved no-regression floors independently: 52.50%
statements and 33.24% branches. The long-term target remains 70% statements
and 60% branches.

Coverage floors move upward only. A reduction requires a separately recorded
parent-level exception with evidence. The current ratchet was approved in
[#358](https://github.com/bettersg/SchemesSG_v3/issues/358#issuecomment-5474089562).

## Test tiers

- `unit`: tests under `tests/unit/`. These do not initialize or contact
  external services.
- `integration`: handler and component tests under `tests/integration/`.
  Firebase, Slack, Azure OpenAI, HTTP, and other external boundaries are
  replaced.
- `smoke`: explicitly marked live checks against a configured
  non-production service. They are opt-in and excluded from the canonical
  secretless suite. No live smoke tests are currently collected.

Run a tier without coverage:

```bash
uv run --frozen pytest -m unit --no-cov
uv run --frozen pytest -m "integration and not smoke" --no-cov
uv run --frozen pytest -m smoke --no-cov
```

Never point smoke tests at production.

## Legacy chat test disposition

`functions/chat/chat.py` was removed in commit `4bee7fd`, but its integration
test still imported that deleted module. `test_chat.py` now preserves the
same handler-level intent against `agent_chat_message`: warmup, method and
payload validation, authentication, generated sessions, successful text,
streaming response type, runtime failure, and CORS preflight.

The old `Chatbot` singleton was removed with the `ml_logic` package, and
`tests/unit/test_chatbot_manager.py` went with it; the agent handler is the only
chat implementation left. The removed endpoint's direct `userQuery` Firestore
lookup and agency/planning-area filtering no longer exist in the current
handler, so those assertions were not recreated.
Detailed stream-event ordering, terminal events, cancellation, and broader
error contracts remain deferred to #371.

## Enforced coverage baseline

Measured on 2026-08-31 from clean integrated `stg` commit `5163173` with
CPython 3.12.11 and branch measurement enabled:

| Metric | Covered / total | Measured | Enforced floor | Target |
| --- | ---: | ---: | ---: | ---: |
| Statements | 2,170 / 4,133 | 52.50% | 52.50% | 70% |
| Branches | 383 / 1,152 | 33.25% | 33.24% | 60% |

The measured branch value is 33.2465%; the approved two-decimal floor is
33.24%. That snapshot was taken when the totals were tight enough that losing
one covered statement or branch without an offsetting gain failed the checker.

Removing `schemes_search` and the `ml_logic` package deleted far more uncovered
code than covered code, so the totals dropped to 3,736 statements and 1,022
branches and the measured values rose to 55.70% and 39.73%. The floors are
unchanged, so there is now headroom; re-baseline them in a dedicated change
rather than silently absorbing the slack.

### Historical pre-ratchet runtime

Measured on 2026-08-29 on macOS arm64 with CPython 3.12.11, pytest 9.1.1,
and no secret environment values. Wall time is from `/usr/bin/time -p`.

| Command | Result | Pytest time | Wall time |
| --- | ---: | ---: | ---: |
| `uv run --frozen pytest -m unit --no-cov -q` | 105 passed | 2.44s | 3.48s |
| `uv run --frozen pytest -m "integration and not smoke" --no-cov -q` | 79 passed | 2.45s | 3.49s |
| `uv run --frozen pytest` | 184 passed, 49% statement coverage | 4.53s | 5.66s |

The full baseline covers 4,117 statements with 2,101 missed. This is the
starting point for later coverage-expansion tickets, not a target reduction.

Exact #381 clean-checkout and CI timings are recorded in the pull request.
Update the enforced table only when an integrated measurement raises a floor.
