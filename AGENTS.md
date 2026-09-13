# SchemesSG v3

Agent-agnostic instructions. `CLAUDE.md` at root, `backend/`, and
`frontend/` symlinks to the colocated `AGENTS.md`; edit the source, not the symlink.

## Read for the task

- For `backend/` or `frontend/` work, read its `AGENTS.md` alongside this file;
  nested instructions may not load automatically.
- For architecture or product decisions, read `DESIGN.md`, `PRODUCT.md`, and
  relevant accepted decisions in `docs/adr/`.
- For required checks, test impact, and evidence, read `docs/verification.md`
  before choosing checks. Load other references when relevant.

## Task isolation and delivery

Repository changes require a dedicated worktree and branch; read-only research
is exempt.

- Create with `scripts/worktree-create.sh <branch> [path]` (also pushes the empty
  task branch), then run `scripts/worktree-preflight.sh` in that worktree before
  editing. Use `--help` for flags; create task branches only through this script.
- Base: freshly fetched `origin/stg`; PR to `stg`, then `stg` → `main` for
  production. `origin/main` requires `--hotfix` for an approved production fix.
- Never commit or push from the user's shared checkout.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, …), imperative
  one-liner, no co-author/signature lines. Semantic-release bumps versions from
  `feat:`/`fix:` and breaking changes.
- For PRs, fill every section of `pull_request_template.md` with the required
  user flow, isolation, test impact, evidence, proof of fix, and caveats.
- When the PR merges or closes, remove its worktree before the session ends:
  `scripts/worktree-lifecycle.sh remove <path>` from another checkout. After an
  interruption or move, use `doctor` on that script for read-only diagnostics.

## Implementation and completion

- For implementation, define observable acceptance criteria and continue through
  the scoped change, verification, and fixes for regressions it causes.
- Run focused checks while iterating, then all required scope checks. Broaden or
  repeat only for new changes, failures, or unresolved concerns.
- Done means a reviewable diff and acceptance evidence. Report checks run,
  checks skipped with reasons, and unresolved risks.
- If blocked by missing access, conflicting instructions, or an action outside
  the request, name the blocker and decision needed; cite the exact file and rule
  for instruction-based blockers.

## Safety

- Production: `schemessg` (`main`). Development: `schemessg-v3-dev` (`stg`).
- Never commit secrets, `.env*`, service-account credentials, or production
  data/exports; exact exclusions are in scoped instructions and gitignore files.
- Deterministic PR checks are secretless. Credentialed Firebase/vector-search
  smoke must use development, never production credentials or data.
- Changes to API contracts, auth, streaming, env/runtime wiring, Compose, or
  cross-stack journeys require development search smoke when they affect real
  Firebase/search wiring; follow `docs/verification.md`.
- Before changing harness, CI, dependency manifests, deployment, or secret
  boundaries, read `.github/CODEOWNERS` for ownership/review requirements.

## Maintaining these instructions

Keep shared, non-obvious rules here; scope domain rules to the domain's file.
Link detailed procedures with a read condition instead of copying them. Keep
personal preferences and agent-specific configuration out of shared policy.
