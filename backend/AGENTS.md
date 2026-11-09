# SchemesSG v3 Backend

Firebase Functions (Python 3.10, `uv`) + scheme-processor (Cloud Run,
Python 3.11). See root `AGENTS.md` for shared worktree, branch, safety, and
evidence policy. Full architecture and API reference: `README.md`.

## Package Manager

Use `uv` only — never bare `python`/`pip`. `uv run --frozen pytest`,
`uv sync`, `uv run python scripts/...`. Canonical pytest config lives in
`pyproject.toml`; tiers are documented in `tests/README.md`.

## Two Dependency Files Must Stay in Sync

`pyproject.toml` (local dev/test, `uv`) and `functions/requirements.txt`
(Firebase Functions deploy) declare overlapping runtime dependencies
independently. When adding/upgrading a dependency used by `functions/`, add
the same package and version to **both** files, then `uv sync`. Firebase
deploy reads only `requirements.txt`; `uv` reads only `pyproject.toml` — one
without the other silently diverges dev from deployed behavior.

## Two Firebase Projects — Never Mix Credentials

- **Production** (`schemessg`): real user data, `functions/.env.prod`. Use
  only for the documented download step; never point local dev, tests, or
  the emulator at it, and never load it into any environment except via
  the download → load workflow in `README.md`.
- **Development** (`schemessg-v3-dev`): `functions/.env` / `.env.dev`.
  Local emulator, development, testing.
- The Firestore emulator runs in single-project mode: importing production
  data while running as `schemessg-v3-dev` writes documents the UI won't
  show. Use the download-to-JSON → load intermediary in `README.md`, never
  a direct cross-project import.
- Never commit `functions/.env*`, `functions/creds*.json`, or
  `prod_schemes_data.json` — see root `.gitignore`.

## Secrets

Tokens move one at a time from the `FUNCTIONS_ENV_VARS*` GitHub secrets (and
the local `.env.*` files `scheme-processor/deploy.sh` reads) to Secret
Manager. To move one:

- Declare it in `bettersg/schemessg-infra` `envs/{dev,production}/secrets.tf`
  (ID = env var name), apply, then add each project's value (infra README).
- Functions: list it in `secrets=[...]` on every function that reads it. Code
  keeps using `os.getenv`; a function that doesn't list it gets `None`.
- Cloud Run job: add it to `JOB_SECRET_KEYS` in `scheme-processor/deploy.sh`.
- Remove it from `FUNCTIONS_ENV_VARS*` before the deploy that declares it:
  Firebase won't deploy a name that is both an env var and a secret.
- Read access goes to the default compute service account. A function with its
  own `service_account` needs its own grant in `secrets.tf`.

## Verification

- Focused pytest file while developing, then `uv run --frozen pytest`
  (secretless suite) before handing off.
- Exercise the changed handler/service on an observable runtime path
  (emulator or unit-level call), not just green tests.
- Scope matrix and evidence fields: `docs/verification.md` (root).

## Pointers

- Architecture, endpoints, scripts, deployment: `README.md`.
- Script details: `scripts/README.md`.
- Test tiers and secretless-suite guarantees: `tests/README.md`.
