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

The Compose stack builds the real Firebase Functions and Next.js applications. Functions run locally but connect to the shared development Firestore because the emulator does not provide the vector-search behavior used by production search. Playwright opens the actual search page, submits a query, and requires one or more real scheme results. Health checks bound startup; failures retain Compose logs, Playwright traces, and screenshots. Cleanup removes task containers and networks without deleting external data.

The default frontend URL is `http://localhost:3000`, matching the backend's checked-in CORS allowlist. Override the port only after adding the corresponding local origin to the development CORS configuration.

## Safety and limitations

This is a **credentialed development smoke tier**, not a secretless PR check. It reads the shared development database and must not write production data. Results can change as the dev dataset changes. GitHub CI runs deterministic secretless unit/integration/E2E tests instead; it validates the Compose definition but cannot execute this credentialed journey for forked pull requests.

A fully local deterministic database/search path is tracked in #393. Until that exists, this smoke is the honest proof for Firestore vector search and environment wiring.
