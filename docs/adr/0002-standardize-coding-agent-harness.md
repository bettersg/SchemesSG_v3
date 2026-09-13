# Standardize the coding-agent harness on scoped AGENTS.md files and task worktrees

## Status

Accepted

## Date

2026-08-29

## Context

SchemesSG used root, backend, and frontend `CLAUDE.md` files. Codex natively discovers `AGENTS.md`; maintaining separately authored Codex and Claude files would duplicate high-impact safety policy. Repository-changing tasks also need isolation from the user’s shared checkout. Normal changes integrate through `stg`, while generic worktree tooling may select the remote default branch instead.

The search implementation uses Firestore vector search. The local Firestore emulator does not provide sufficient parity, so an honest end-to-end search smoke must use the shared `schemessg-v3-dev` database. Deterministic secretless tests remain the PR gate; development-account smoke is a separate credentialed tier.

## Decision

- Author `AGENTS.md` at root, backend, and frontend; make each colocated `CLAUDE.md` a relative symlink.
- Require repository-changing tasks to use a task worktree based on freshly fetched `origin/stg`. `origin/main` requires explicit hotfix mode.
- Enforce the worktree invariant with a checked-in preflight interface and tests.
- Preserve deterministic secretless unit/integration/browser PR tests.
- Add a health-driven development smoke stack using the real frontend, real Firebase Functions, and `schemessg-v3-dev`; require an actual search result.
- Keep shared rules at root and scoped differences near governed code; point to executable/configuration sources rather than copying inventories.

## Alternatives

### Separately authored AGENTS.md and CLAUDE.md

Rejected because duplicated safety and verification policy would drift. Reconsider only if a supported environment cannot use repository symlinks and generated-file checks can guarantee synchronization.

### Root-only instructions

Rejected because backend production-data safety and frontend UI verification are genuine scoped differences. A root-only file would either bloat or hide them.

### Deterministic fake backend as full-stack search proof

Rejected because it proves HTTP/UI wiring but not Firebase configuration, vector search, or the development dataset. Existing Playwright tests already cover deterministic frontend behavior more honestly.

### Local Firestore emulator as search proof

Deferred because vector-search parity is insufficient. A local data/search strategy is tracked in #393.

## Consequences

- Codex and Claude consume one authored source per scope.
- Preflight protects the shared checkout and records the chosen base SHA.
- Worktrees still share ports, Compose resources, caches, refs, credentials, and external services; runtime resources must be namespaced or serialized.
- The development smoke is read-oriented but credentialed and non-deterministic because shared dev data can change.
- Production credentials and production data are forbidden from smoke.
- Harness, workflow, dependency, deployment, and secret-boundary files require ownership and mechanical checks.

## Verification

- Exercise instruction discovery from fresh root, backend, and frontend sessions in Codex and Claude.
- Test preflight success in a valid task worktree and failure in shared-checkout and invalid branch/upstream/base cases.
- Run deterministic secretless backend/frontend suites.
- Start the health-checked development stack, submit a browser search, and observe at least one result from `schemessg-v3-dev`.
- Apply `docs/verification.md` and record proof in the pull request template.

## Review triggers

Revisit when the integration branch changes, a required agent cannot follow the symlink layout, local vector-search parity becomes available, or shared development data becomes unsuitable for smoke testing.
