# Backend test suite

Run the canonical secretless suite from `backend/`:

```bash
uv run --frozen pytest
```

`pyproject.toml` is the single pytest configuration source. It controls
discovery, import paths, strict marker registration, warning filters, the
default smoke-test exclusion, and coverage.

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

The old `Chatbot` singleton and response behavior remains covered in
`tests/unit/test_chatbot_manager.py`. The removed endpoint's direct
`userQuery` Firestore lookup and agency/planning-area filtering no longer
exist in the current handler, so those assertions were not recreated.
Detailed stream-event ordering, terminal events, cancellation, and broader
error contracts remain deferred to #371.

## Baseline

Measured on 2026-08-29 on macOS arm64 with CPython 3.12.11, pytest 9.1.1,
and no secret environment values. Wall time is from `/usr/bin/time -p`.

| Command | Result | Pytest time | Wall time |
| --- | ---: | ---: | ---: |
| `uv run --frozen pytest -m unit --no-cov -q` | 102 passed | 2.42s | 3.47s |
| `uv run --frozen pytest -m "integration and not smoke" --no-cov -q` | 79 passed | 2.42s | 3.46s |
| `uv run --frozen pytest` | 181 passed, 49% statement coverage | 4.20s | 5.20s |

The full baseline covers 4,114 statements with 2,105 missed. This is the
starting point for later coverage-expansion tickets, not a target reduction.
