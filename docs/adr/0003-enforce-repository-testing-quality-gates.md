# Enforce repository testing quality gates

## Status

Accepted

## Date

2026-08-31

## Context

Parent issue #358 established a layered, secretless test system. Its focused
tickets added backend contracts, frontend unit and integration coverage,
critical Chromium journeys, pull-request CI, and nightly cross-browser and
deployed-staging checks. The final rollout must make those checks enforceable
without weakening existing branch protection.

Frontend coverage already exceeds the agreed 70% statements, functions, and
lines and 60% branches. Its unit/integration and PR browser lanes have separate
120-second budgets. The clean backend measurement at integrated `stg` commit
`5163173` was 52.50% statements and 33.24% branches. Reaching 70/60 in this
final-gates issue would require broad shallow test work, so the parent approved
an independent no-regression ratchet for #381.

The agent harness also required an explicit test-impact contract: every
observable behavior change must map to focused regression coverage or an
explicit no-test reason and substitute evidence.

Baseline repetition also exposed an intermittent accessibility failure: the
chat recovery journey could scan a follow-up control during its opacity
entrance even though the PR browser requests reduced motion. Final browser-job
consistency therefore requires that control to use a static reduced-motion
state while preserving the Axe assertion.

## Decision

- `docs/verification.md` is the authoritative source for local test tiers,
  change-scope evidence, and test-impact policy.
- Frontend coverage keeps global floors of 70% statements, functions, and
  lines and 60% branches. Unit/integration coverage and PR Chromium remain
  independently bounded to 120 seconds.
- Canonical backend runs measure branches and enforce independent minimums of
  52.50% statements and 33.24% branches. The checker fails if either metric
  regresses. The target remains 70% statements and 60% branches.
- Backend floors move upward only. Any reduction requires a separately
  recorded parent-level exception with evidence. The approval is recorded on
  [#358](https://github.com/bettersg/SchemesSG_v3/issues/358#issuecomment-5474089562).
- Pull requests to `stg` and `main` continue to produce the stable `Frontend
  quality`, `Frontend E2E`, and `Backend tests` contexts in parallel. Those
  three contexts are required on both branches.
- Required checks are added to the existing classic branch-protection rules.
  Reviews, admin enforcement, restrictions, strictness, existing rulesets, and
  unrelated settings remain unchanged.
- `Harness integrity` remains a path-scoped check rather than a required
  context because it is not emitted for every pull request.
- The pull-request template records test impact and reviewer confirmation.
  Harness integrity mechanically protects the authoritative heading and
  required fields, and CODEOWNERS covers those control files.

## Alternatives

### Raise backend coverage to 70/60 in #381

Rejected. The approved baseline would require at least 724 additional covered
statements and 309 additional covered branches across broad runtime modules.
Percentage-only tests would conflict with the parent testing policy.

### Enforce one combined backend percentage

Rejected. Statement gains could hide a branch regression or vice versa.
Independent floors make each approved dimension non-regressing.

### Require the path-scoped harness job

Rejected. Pull requests outside its path filter would never emit that context
and could remain blocked indefinitely.

## Consequences

- Contributors can reproduce every required job locally from documented
  lockfile-based commands.
- Backend branch coverage is now visible and independently protected while
  focused future tickets raise both floors toward 70/60.
- A pull request cannot merge to `stg` or `main` while any stable PR Quality
  context is failing or missing.
- Test additions are judged by behavior and seam relevance, not by a naive
  source-diff/test-file-diff rule.

## Verification

- Run the harness and mutation-check removal of the test-impact policy heading
  and required PR fields.
- Run frontend lint, typecheck, coverage, production build, PR Chromium,
  nightly cross-browser, and read-only staging tiers from a clean checkout.
- Run the canonical backend suite, export coverage JSON, and pass it through
  the independent ratchet checker. Mutation tests prove each floor fails.
- Record GitHub job and workflow durations from a cold pull-request run.
- Capture branch-protection API state before and after adding the three stable
  contexts, then demonstrate a required failing context blocks merge and
  restore the pull request to green.

## Review triggers

Revisit when backend coverage supports higher floors, stable PR job names
change, the branch model changes, or the harness test-impact fields change.
