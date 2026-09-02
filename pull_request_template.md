## Problem

Closes #

Describe the user or engineering problem.

## Changes

Describe the scoped change and why this approach was chosen.

## Task isolation

- Worktree:
- Branch:
- Base ref and SHA:
- Shared surfaces changed (instructions, workflows, dependencies, Compose, schemas, fixtures):

## Test impact

- Observable behavior changes:
- Focused regression tests:
- Red-before evidence (bug fixes, when practical):
- Green-after evidence:
- No-test reason (if applicable):
- Substitute evidence (if applicable):

## Verification evidence

| Scope | Exact command or scenario | Result | Duration |
|---|---|---|---|
| Static/scoped checks |  |  |  |
| Behavioral smoke |  |  |  |
| Browser/UI proof, when applicable |  |  |  |

- Acceptance criteria demonstrated:
- Checks intentionally not run and why:

### Proof of fix

Artifacts showing the change working, not only checks passing. Say what each one
proves and how it was captured.

- Failure reproduced (before):
- Same command or request succeeding (after):
- Screenshots, traces, or logs:
- Not capturable pre-deploy, and the signal to watch instead:

## Risks and follow-up

- Unresolved risks:
- Follow-up issues:

## Reviewer checklist

- [ ] Diff is scoped to the linked issue.
- [ ] Test impact accounts for every observable behavior change.
- [ ] Evidence covers the changed public behavior.
- [ ] Cross-boundary changes include full-stack smoke proof.
- [ ] No secrets, production data, or unrelated generated artifacts are included.
