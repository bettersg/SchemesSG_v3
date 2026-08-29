# ADR 0001: Frontend testing foundation

- Status: Accepted
- Date: 2026-08-29

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
- Unit tests live beside the module as `*.test.ts(x)`. Integrated flows live in
  `src/test/integration` as `*.integration.test.tsx`.
- Coverage is reported on demand without thresholds. Threshold enforcement is
  deferred to #378.

The supported commands are:

| Purpose | Command |
| --- | --- |
| Full unit and integration run | `npm test` |
| Unit run | `npm run test:unit` |
| Integration run | `npm run test:integration` |
| Watch mode | `npm run test:watch` |
| Coverage report | `npm run test:coverage` |
| Type checking | `npm run typecheck` |
| Linting | `npm run lint` |
| Production build | `npm run build` |

## Consequences

- Contributors get one fast, secretless feedback loop based on npm.
- Browser journeys remain the responsibility of #374. Coverage gates and PR
  workflows remain the responsibility of #378 and #379.
- Async Server Components are not simulated in jsdom; they remain browser-test
  seams.
