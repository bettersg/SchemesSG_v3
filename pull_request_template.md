<!-- The whole description's target audience is humans, not AI agents: write it in plain, simple,
     everyday engineering language, extremely parsable and readable at a glance. This goes double for
     the TLDR, User Flow, and Caveats sections -->

## TLDR

<!-- Fill in the bullets below and keep each one short and concrete: one line per bullet, roughly 10 words max -->

Problem this solves:

- <blah>
- ...

How it solves it:

- <blah>
- ...

## User Flow

<!-- Two ordered lists, Before and After, walking the same end user through the same task, written strictly from that user's seat
     Read the linked issue, ticket, or user report first so the flow reflects the real application and the routes its users actually hit; don't invent a generic scenario
     Lead each list with one plain sentence saying where the flow fails (Before) or succeeds (After), then number the steps
     Every step is something the user does or observes: the page URL they open or the HTTP method and full URL they hit, what they sent, and what visibly came back (status code, error text, what appeared on screen)
     No SchemesSG internals: never name functions, files, Firestore collections, config classes, hooks, contexts, or code paths. "The chat column stays completely empty for twelve seconds after they hit send" is right, "isGenerating was still false" is wrong
     Keep the two lists step-for-step identical until they diverge, so the changed step is obvious
     If the bug had a security or authorization consequence, end each list with what another user could or could no longer do
     Regenerate this section whenever new commits change the PR's behavior, so it never describes an older revision

Example:

Before: someone searching for help gets no sign the app heard them, so they hit send again

1. They open https://schemes.sg/ and type "help with rent for my elderly mother" into the search box
2. They press Enter and the page transitions to the chat view with an empty column
3. Nothing at all appears for about twelve seconds, so they assume it broke and re-send

After: the same search shows a thinking indicator immediately, so they wait instead of re-sending

1. They open https://schemes.sg/ and type the same query into the search box
2. They press Enter and within half a second a spinner and a "Reading your question" line appear
3. The line updates to "Searching schemes database", then to "142 schemes found", then the answer streams in
-->

## Relevant issues

<!-- e.g., "Closes #000" -->

## Task isolation

<!-- Required by AGENTS.md: every change to tracked files runs in its own worktree on its own branch -->

- Worktree:
- Branch:
- Base ref and SHA:
- Shared surfaces changed (instructions, workflows, dependencies, Compose, schemas, fixtures):

## Test impact

<!-- Account for every observable behavior change; see docs/verification.md for the policy -->

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

## Pre-Submission checklist

**Please complete all items before asking a maintainer to review your PR**

- [ ] I have added meaningful tests
- [ ] The handful of test files covering my change pass locally, e.g. `pytest backend/functions/tests/<your_test_file>.py -v` or `npx vitest run src/<your_test_file>.test.tsx`. Leave the full suites to CI
- [ ] My PR passes all required CI/CD checks (Frontend quality, Frontend E2E, Backend tests, CodeQL, GitGuardian, Harness integrity)
- [ ] My PR's scope is as isolated as possible; it only solves 1 specific problem
- [ ] No secrets, `.env*` files, service-account credentials, or production data are in the diff

## Screenshots / Proof of Fix

<!-- Include screenshots, screen recordings, or command + output demonstrating that your changes work as expected
     The proof must be completely e2e with no mocks, against a real running stack (development `schemessg-v3-dev`, never production). `pytest` and `vitest` runs are not enough
     Attach images and recordings to the PR with `gh pr edit <number> --body-file <file> --attach './path/shot.png#alt text'`; reference the same local path in the body and the CLI rewrites it in place. Never commit them to the repository
     Show ONLY the latest run: capture Before at the merge base and After at the PR's current tip, and when new commits change behavior, replace this whole section with the fresh run instead of stacking it on top of older ones. The run must be up to date. As soon as a new commit makes this PR description's after sha stale (it's no longer tip of PR), you must re-run the QA
     Structure the section exactly as below: Before and After one heading level below this section, each naming the commit hash it was captured at, one lower-level heading per case inside each, the same case names in the same order on both sides, and numbered steps (command, observed output) under every case, never loose prose; shared setup (config, payloads) goes above Before, and with a single case, drop the case headings and number the steps directly

### Before (<hash>)

#### <case 1>

1. ...
2. ...

#### <case 2>

1. ...

### After (<hash>)

#### <case 1>

1. ...
2. ...

#### <case 2>

1. ...

     For bug fixes: Before shows the reproduction, After shows the same steps passing
     For new features: Before shows the capability missing, After shows it working end-to-end
     For cross-boundary changes (API contract, auth, streaming, env/runtime wiring, Compose, or a journey spanning frontend and backend), make the frontend page and the backend endpoint each their own case, not just one
     For UI changes: before/after screenshots or recordings under the same headings -->

## Type

<!-- Select the type of Pull Request -->
<!-- Keep only the necessary ones -->

🆕 New Feature
🐛 Bug Fix
🧹 Refactoring
📖 Documentation
🚄 Infrastructure
✅ Test

## Caveats (if any)

<!-- Group caveats under severity subheadings (### Severe, ### High, ### Medium, ### Low), with
     short bullet points inside each, just like the TLDR: one line per bullet, roughly 10 words max
     Call out known limitations, follow-up work, or anything a reviewer should watch out for
     Include only the tiers that have caveats; drop the empty ones
     - Severe: inherent to what the PR deliberately ships, there even when the code works as intended:
       it can degrade or take down a running deployment (e.g. a slow or index-rebuilding migration),
       rewrite data by design, break an existing workflow on purpose, or change auth behavior. An
       operator must plan around it before rollout
     - High: an unintended hole: a correctness, security, data-loss, or backward-compatibility bug,
       unsafe to ship as is
     - Medium: a real gap someone can hit, but with a workaround or a narrow blast radius
     - Low: anything else worth noting: naming, cleanup, an edge case nobody hits
     Nest bullets as deep as helps: hierarchy beats one long line when it makes things clearer to a
     human reader
     Leave this section empty if there are none -->

## QA runbook

<!-- Only needed when your PR edits e2e tests; delete this section otherwise

For each e2e test you added or changed, list the manual steps a reviewer can follow to reproduce it by hand against a live stack, mapping 1:1 to what the test asserts: one top-level bullet per test giving its test id (pytest node id, or Playwright file plus test title) followed by what it proves in plain words, then a nested "- [ ]" checklist where each item is a concrete action (page, route, request body, expected response) and the final item is the sanity-check step shown in the example. Note environment prerequisites (Firebase credentials, env flags, Compose services) and any nuances a manual run will hit

Example checklist:

- frontend/e2e/chat-thinking-indicator.spec.ts::shows the indicator before the first status event - a send puts a spinner and a phrase on screen inside a second, with no backend response yet
  - [ ] Bring up the dev-smoke stack: docker compose -f compose.dev-smoke.yml up --wait
  - [ ] Open http://localhost:3000/ and send "help with rent for my elderly mother"
  - [ ] Expect a spinner and a thinking phrase visible under 1s, before any streamed answer text
  - [ ] Sanity check: this test makes sense to add and is not hand-wavey (e.g., assert the indicator's actual first-paint timing instead of just that it eventually appears) or potentially flaky
-->

## Final Attestation

- [ ] The tests check the right things, including the edge cases, and regressions in the respective real-world user journeys are not possible after this PR
