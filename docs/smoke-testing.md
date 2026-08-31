# Development search smoke

Run from a task worktree:

```sh
./scripts/smoke-dev-search.sh
```

The runner locates the primary checkout and mounts its ignored development inputs read-only:

- `backend/functions/.env`
- `backend/functions/creds.json`
- `frontend/.env.staging`

Override `SCHEMESSG_DEV_CONFIG_DIR` or `SCHEMESSG_FRONTEND_ENV` when those files live elsewhere. The runner refuses configurations whose Firebase project is not `schemessg-v3-dev`.

The Compose stack builds the real `scheme-processor`, Firebase Functions, and Next.js applications. Startup is ordered by health: `scheme-processor` → Functions → frontend. The smoke proves the processor's non-mutating `/health` endpoint but does not call `/process`, which would scrape external sites, invoke an LLM, write Firestore, and post to Slack. Functions connect to shared development Firestore because the emulator does not provide the vector-search behavior used by production search. Playwright submits an actual search and requires one or more real scheme results. Failures retain Compose logs, Playwright traces, and screenshots; cleanup removes task containers and networks without deleting external data.

The default frontend URL is `http://localhost:3000`, matching the backend's checked-in CORS allowlist. Override the port only after adding the corresponding local origin to the development CORS configuration.

## Safety and limitations

This is a **credentialed development smoke tier**, not a secretless PR check. It reads the shared development database and must not write production data. Results can change as the dev dataset changes. GitHub CI runs deterministic secretless unit/integration/E2E tests instead; it validates the Compose definition but cannot execute this credentialed journey for forked pull requests.

A fully local deterministic database/search path is tracked in #393. Until that exists, this smoke is the honest proof for Firestore vector search and environment wiring.

## Deployed staging smoke

Run the non-mutating deployed check from `frontend/`:

```sh
npm run test:e2e:staging
```

The target is hard-coded to `https://schemessg-v3-dev.web.app` and cannot be
overridden with an environment variable. The first Playwright project checks
HTTP availability, the final host, expected application metadata, and that the
deployed bundles contain the development Firebase project and Cloud Functions
API origin. The second project runs only after that gate and verifies that the
landing page can navigate to the unselected catalog page.

Both projects load through the same instrumented browser fixture. It blocks
service workers, all off-origin requests, and every request method except GET,
HEAD, and OPTIONS. Allowed and blocked traffic is retained with request methods,
resource types, URLs, and block reasons in a standalone JSON attachment.
Availability failures also retain the page screenshot and trace. The smoke uses
no credential or secret, never submits a search or form, cannot contact the
production host, and cannot write development or production data.

`.github/workflows/nightly-browser.yml` runs this smoke nightly and by manual
dispatch. Availability/configuration and product steps have distinct names so
the failure class is visible before opening the retained report and trace.
