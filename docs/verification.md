# Change verification

Use the smallest check set that proves the changed behavior. Record exact commands, scenarios, results, and durations in the pull request.
Credentialed development search command and limitations: `docs/smoke-testing.md`.


| Change scope | Required evidence |
|---|---|
| Documentation or harness only | Link/symlink integrity, harness preflight tests, and a fresh-session instruction discovery check when instructions change. |
| Backend only | Focused pytest file while developing, then the backend suite. Exercise the changed handler/service when it has an observable runtime path. |
| Frontend only | Focused Vitest file while developing, then lint, typecheck, frontend tests, and build. Visually verify UI changes in a browser. |
| Cross-boundary | Backend and frontend checks plus the credentialed development search smoke when the change affects real Firebase/search wiring. |

A change is cross-boundary when it affects an API contract, authentication, streaming, environment/runtime wiring, Compose, or a user journey spanning frontend and backend.

## Evidence contract

Every pull request records:

- task worktree, branch, base ref, and base SHA;
- changed files and shared control surfaces;
- exact checks and scenarios, results, and durations;
- acceptance criteria demonstrated;
- screenshots, traces, or concise logs for UI/runtime behavior;
- checks not run and the reason;
- unresolved risks and follow-up issues.

“Container started,” “tests pass,” or an agent’s assertion is not proof by itself. Readiness comes from health checks. UI behavior comes from exercising the actual page. Failures must return non-zero and retain enough diagnostics to reproduce them.

Deterministic secretless tests remain the PR gate. Real Firestore vector-search and environment wiring use the separate credentialed development smoke tier; never use production credentials or production data.
