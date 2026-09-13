# SchemesSG v3

Two main folders: `backend/` and `frontend/`. See their `AGENTS.md` for scoped
guidance. `CLAUDE.md` at each of these three locations is a relative symlink
to `AGENTS.md` — edit `AGENTS.md` only, never the symlink.

## Firebase Projects

- **Production**: `schemessg` — deployed from `main` branch
- **Development**: `schemessg-v3-dev` — deployed from `stg` branch

## Task Isolation — REQUIRED for repository changes

Every task that changes tracked (or intended-to-be-tracked) files runs in its
own git worktree on its own branch. Read-only research is exempt.

- Create/verify the worktree with `scripts/worktree-create.sh` and
  `scripts/worktree-preflight.sh` (run `--help` on either for flags). Default
  base is freshly fetched `origin/stg`; `origin/main` requires explicit
  `--hotfix` for an approved production fix.
- Never commit or push from the user's shared checkout.
- Run preflight before editing; it fails fast on the wrong worktree, branch,
  upstream, or base ancestry.
- After merge or abandonment, use `scripts/worktree-lifecycle.sh remove <path>`
  from another checkout. Use `doctor` after interrupted/moved worktrees; it is
  diagnostic and never force-removes, prunes, repairs, or deletes branches.

## Git Workflow

- Branch from `stg`, PR to `stg`, then PR `stg` → `main` for production.
- Commit style: **Conventional Commits** (`feat:`, `fix:`, `chore:`,
  `docs:`, …), imperative mood, one-liner, no co-author/signature lines.
  `release.yml` runs semantic-release, which bumps the version only from
  `feat:`/`fix:` (and `BREAKING CHANGE:`) commits.
- Branch creation is scripted — see `scripts/worktree-create.sh`. Never
  `git checkout -b <new> origin/<base>` by hand; it sets upstream to
  `<base>` and a later bare `push` lands commits on it directly.

## Safety

- Never commit secrets, `.env*` files, service-account credentials, or
  production data/exports. See each domain's gitignore and `AGENTS.md` for
  the exact file list.
- Deterministic PR verification is secretless. Real Firebase/vector-search
  smoke is credentialed, must target development (`schemessg-v3-dev`), and
  must never use production credentials or data.
- Harness, CI workflow, dependency-manifest, deployment, and secret-boundary
  files are owned/reviewed per `.github/CODEOWNERS`.

## Verification & Evidence

- Authoritative scope-based checks and test-impact policy:
  `docs/verification.md`.
- Fill in every section of `pull_request_template.md`: TLDR, the before/after
  User Flow written from the user's seat, task isolation (worktree/branch/base
  SHA), test impact, verification evidence, before/after Proof of Fix at named
  commit hashes, and severity-graded caveats.
- Cross-boundary changes (API contracts, auth, streaming, env/runtime
  wiring, Compose, or a journey spanning frontend and backend) additionally
  require the development search smoke when they affect real Firebase/search
  wiring — see `docs/verification.md`.
- "Tests pass" or an assertion is not evidence by itself: readiness comes
  from health checks, UI behavior from exercising the actual page.

## Design & Decisions

- Architecture/product context: `DESIGN.md`, `PRODUCT.md`.
- Accepted decisions: `docs/adr/`.
