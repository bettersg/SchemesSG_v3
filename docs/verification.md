# Change verification

Use the smallest check set that proves the changed behavior. Record exact commands, scenarios, results, and durations in the pull request.
Credentialed development search command and limitations: `docs/smoke-testing.md`.

## Local test tiers

Install from lockfiles before validating a clean checkout: `npm ci` in
`frontend/` and `uv sync --locked` in `backend/`.

| Tier | Purpose | Command |
|---|---|---|
| Harness | Repository instructions and control-file contracts | `./scripts/test-harness.sh` |
| Backend unit | Isolated logic with no external services | `cd backend && uv run --frozen pytest -m unit --no-cov` |
| Backend integration | Handlers and components with external boundaries replaced | `cd backend && uv run --frozen pytest -m "integration and not smoke" --no-cov` |
| Backend canonical | Secretless unit/integration suite with independent coverage ratchets | `cd backend && uv run --frozen pytest && uv run --frozen coverage json -o - \| uv run --frozen python scripts/check_coverage.py` |
| Frontend unit/integration | Vitest, Testing Library, and enforced coverage | `cd frontend && npm run test:coverage` |
| Frontend static/build | Lint, types, and validation build | `cd frontend && npm run lint && npm run typecheck && npm run build` |
| PR browser | Deterministic desktop and mobile Chromium journeys | `cd frontend && npm run test:e2e -- --project=chromium --project=mobile-narrow-chromium` |
| Broader browser | Nightly Chromium, Firefox, and WebKit journeys | `cd frontend && npm run test:e2e:nightly` |
| Deployed staging | Read-only development-host smoke | `cd frontend && npm run test:e2e:staging` |
| Development search smoke | Credentialed frontend, Functions, processor, and vector-search wiring | `./scripts/smoke-dev-search.sh` |

Backend smoke tests are opt-in and must target a configured non-production
service: `cd backend && uv run --frozen pytest -m smoke --no-cov`. The canonical
backend suite excludes them. Frontend watch mode is
`cd frontend && npm run test:watch`. See `backend/tests/README.md` and the
frontend testing ADR for each suite's detailed boundaries.

## Test impact

Every pull request accounts for every observable behavior change. Map each
behavior to a new or updated focused regression test at the narrowest public
seam. For bug fixes, record red-before and green-after evidence when practical.

If automated tests do not change, name the behavior or non-behavior change,
give a specific no-test reason, and provide substitute verification evidence.
Documentation-only and mechanical changes are valid no-test cases when that
reason is explicit. Reviewers judge whether the mapped test is relevant; the
harness does not infer test impact from source-file and test-file diffs.

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
- test-impact mapping, including red/green evidence or a no-test reason and substitute evidence;
- exact checks and scenarios, results, and durations;
- acceptance criteria demonstrated;
- proof of fix: the failure reproduced, then the same command or request succeeding;
- screenshots, traces, or concise logs for UI/runtime behavior, attached to the
  pull request rather than committed — image and trace files do not belong in the
  repository, where they outlive the review that needed them and are never read
  again;
- checks not run and the reason;
- unresolved risks and follow-up issues.

“Container started,” “tests pass,” or an agent’s assertion is not proof by itself. Readiness comes from health checks. UI behavior comes from exercising the actual page. Failures must return non-zero and retain enough diagnostics to reproduce them.

### Where screenshots live

Drag-and-drop upload into a comment is the normal route, but it needs a browser —
there is no API for it, so an agent cannot do it. Rather than commit the files or
leave a UI change unevidenced, push them to a **gist** and link them:

```sh
gh gist create notes.md                      # gh cannot take binaries; seed with any text file
git clone https://gist.github.com/<id>.git   # a gist is a git repo, so push images through git
cd <id> && cp /path/to/*.png . && git add -A && git commit -m "evidence" && git push
```

Embed with the URL pinned to the pushed commit, so the image cannot change under a
reviewer after approval:

```
![what it shows](https://gist.githubusercontent.com/<user>/<id>/raw/<sha>/shot.png)
```

Two details that are easy to get wrong. The unpinned `raw/<file>` form returns 404
for a binary, so the SHA is required, not optional. And gist URLs render directly
rather than through GitHub's image proxy, so a missing image means a bad URL, not a
proxy failure — `gh api -H "Accept: application/vnd.github.full+json" …` and grep
the returned `body_html` for `<img` to confirm, because `body_html` is null without
that header.

A gist is deliberately impermanent: delete it and the images 404. That suits review
evidence, which stops being true the moment the page changes. Anything that needs to
stay true belongs in a test instead.

Deterministic secretless tests remain the PR gate. Real Firestore vector-search and environment wiring use the separate credentialed development smoke tier; never use production credentials or production data.
