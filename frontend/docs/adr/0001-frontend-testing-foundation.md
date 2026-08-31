# ADR 0001: Frontend testing foundation

- Status: Accepted
- Date: 2026-08-29
- Last amended: 2026-08-31 (#380)

## Context

The frontend had no unit or integration runner. Package-manager artifacts also
disagreed with the npm-based build and deployment paths. Tests must be fast,
deterministic, and runnable without Firebase or API credentials.

## Decision

- npm is the only frontend package manager. `package-lock.json` is authoritative
  and clean installs use `npm ci`.
- Vitest runs TypeScript tests in jsdom. React Testing Library, user-event, and
  jest-dom are the component-testing interface.
- Unit tests exercise public pure seams. Initial seams cover scheme mapping and
  contact cleanup, scheme filtering, category and SEO helpers, chat storage
  serialization, and SSE parsing.
- Integration tests render real providers and page-level client components.
  Firebase is replaced only at `auth-gateway.ts`, and HTTP is intercepted by
  deterministic MSW handlers.
- Unhandled HTTP requests fail tests. The suite never calls Firebase, deployed
  APIs, or production services.
- Firebase App/Auth initialization occurs only when the auth gateway is used.
  Secretless validation builds skip remote sitemap entries and contact neither
  Firebase nor a deployed API; deployable builds still receive environment
  configuration from the deployment path.
- Unit tests live beside the module as `*.test.ts(x)`. Integrated flows live in
  `src/test/integration` as `*.integration.test.tsx`.
- Coverage includes untested runtime files and enforces global floors of 70%
  for statements, functions, and lines and 60% for branches.

## Coverage measurement policy

`src/**/*.{ts,tsx}` is measured by default. The allowlist is expressed as
named exclusions in `vitest.config.mts`; a module is never excluded merely
because it is uncovered.

Critical runtime behavior stays measured. This includes all hooks and
providers; authentication and Firebase initialization; scheme retrieval,
mapping, filtering, and detail behavior; chat storage, streaming, state, and
orchestration; catalog state; language state; the navbar; and feedback and
contribution forms. Async Server Components continue to run at the browser
seam.

The exclusion categories are:

| Category                    | Files                                                                                                                            | Reason                                                                                                                                   |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Test support                | `src/test/**`                                                                                                                    | Fixtures, MSW setup, and test harnesses are not shipped runtime behavior.                                                                |
| Static configuration        | The named landing-agency data, design tokens, motion constants, and translation catalogs                                         | These modules are declarative data with no domain or state decisions.                                                                    |
| Next.js/browser entrypoints | The individually named root/route layouts, metadata routes, async catalog pages, async scheme page, and landing page entrypoints | React Server Components and framework metadata lifecycle are not simulated in jsdom; their output is covered by Playwright.              |
| Visual-only modules         | The individually named animation components                                                                                      | Timing, layout, and paint are browser concerns; these modules own no product or domain state.                                              |
| Presentational UI           | The individually named landing sections/primitives, layout wrappers, and skeletons                                              | These modules arrange copy, run self-contained visual demos, or render placeholders. Interactive product and domain state stays included. |

Every non-test exclusion is listed as a concrete file in `vitest.config.mts`,
apart from the route-safe wildcard needed to match Next.js route-group names.
Adding an exclusion requires updating this policy with the category and test
seam that owns the behavior.

## Runtime and visual-baseline policy

- PR unit/integration coverage and Chromium E2E are separate parallel jobs.
  Their stable job IDs and display names remain `frontend-quality` / Frontend
  quality and `frontend-e2e` / Frontend E2E.
- Each test command, including Playwright web-server startup, is measured and
  terminated at 120 seconds. CI writes the measured duration to the step
  summary and emits an error annotation with the local reproduction command on
  timeout or failure. Dependency installation and production build are outside
  the test-lane measurement.
- PR E2E runs both current Chromium projects: desktop Chrome and Pixel 10.
- Normal Playwright runs set `updateSnapshots: "none"`; CI can neither create
  missing goldens nor update changed goldens.
- `npm run test:e2e:update-snapshots` is the only supported update command.
  Run it in the target platform, inspect the image diff, and commit the result
  explicitly. Linux baselines retain Playwright's existing `-linux.png`
  convention and must be generated in a matching Linux environment.

## Nightly and deployed-staging policy

- `playwright.nightly.config.ts` inherits the deterministic local-server
  harness and replaces only its project list. Every desktop journey runs in
  Chromium, Firefox, and WebKit. Mobile Chromium stays in the PR lane.
- Firefox and WebKit set `ignoreSnapshots: true`. Chromium remains the sole
  owner of the reviewed visual baselines, and every configuration keeps
  `updateSnapshots: "none"`.
- `.github/workflows/nightly-browser.yml` has only `schedule` and
  `workflow_dispatch` triggers. It does not add Firefox, WebKit, or deployed
  staging to ordinary pull-request runs.
- Deployed staging is fixed to `https://schemessg-v3-dev.web.app`. The smoke
  accepts no environment override, credentials, secrets, or production host.
  Service workers are blocked. Browser routing aborts all off-origin traffic
  and every request except GET, HEAD, and OPTIONS before it reaches the
  network.
- Staging availability/configuration and product behavior are separate
  Playwright projects. The product project depends on the availability gate,
  which also verifies the deployed development Firebase project and API origin,
  then checks only the landing and unselected catalog routes. It does not submit
  search, feedback, or contribution data.
- Failed cross-browser and staging runs upload their HTML report, screenshots,
  traces, and read-only network log for seven days.

The supported commands are:

| Purpose                         | Command                             |
| ------------------------------- | ----------------------------------- |
| Full unit and integration run   | `npm test`                          |
| Unit run                        | `npm run test:unit`                 |
| Integration run                 | `npm run test:integration`          |
| Watch mode                      | `npm run test:watch`                |
| Coverage report                 | `npm run test:coverage`             |
| Chromium browser run            | `npm run test:e2e`                  |
| Nightly cross-browser run        | `npm run test:e2e:nightly`          |
| Deployed staging smoke           | `npm run test:e2e:staging`          |
| Explicit visual-baseline update | `npm run test:e2e:update-snapshots` |
| Type checking                   | `npm run typecheck`                 |
| Linting                         | `npm run lint`                      |
| Production build                | `npm run build`                     |

## Consequences

- Contributors get one fast, secretless feedback loop based on npm.
- Browser journeys remain the responsibility of #374-#377. Coverage gates and
  PR runtime enforcement are owned by #378; the secretless workflow foundation
  remains owned by #379.
- Async Server Components are not simulated in jsdom; they remain browser-test
  seams.
