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

Everything comes from `functions/.env` (the `FUNCTIONS_ENV_VARS*` GitHub
secrets when deployed) except the names below, which come from Secret Manager
(`bettersg/schemessg-infra`):

- Functions: names in a function's `secrets=[...]`. They must not also be in
  `.env`, or Firebase won't deploy. Locally, put them in
  `functions/.secret.local` (gitignored); without it they are unset.
- Content check job: `JOB_SECRET_KEYS` in `scheme-processor/deploy.sh`. The
  Functions can keep the same name in `.env`; the two don't clash.

To move a token: declare it in infra `envs/*/secrets.tf` and add its values,
list it as above, then remove it from `FUNCTIONS_ENV_VARS*`.

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
