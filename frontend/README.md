# 🚀 SchemesSG V3 Frontend

Welcome to the Next.js frontend for SchemesSG V3! Let's build something awesome together.

## 📚 Quick Navigation
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Key Scripts](#key-scripts)
- [Testing](#testing)
- [Workflow & Contributing](#workflow--contributing)
- [Deployment](#deployment)
- [Environment](#environment)
- [URLs](#urls)

## Prerequisites

Before we dive in, make sure you've got:
- 💻 Node.js (v20.19 or later)
- 📦 npm (v10 or later)
- 🐙 Git

## Quick Start

1. **Setup (Let's get this party started!)**
   ```bash
   cd frontend
   npm ci
   ```

   npm is the only supported frontend package manager. Commit changes to
   `package-lock.json`; do not replace it with another lockfile.

   > 🔑 **Important**: Download the environment files (.env.*) from [Google Drive](https://drive.google.com/drive/u/2/folders/1RtqR8vZtjMrgqIGa-uQEZJa9x4dL3z4U) and place them in the frontend root directory before running the app or creating a deployable build. Unit tests, integration tests, and validation builds do not need these files.

2. **Frontend-only development**
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000`. Use this for UI work; deterministic unit/integration/E2E tests replace Firebase and backend boundaries. A live local backend is not required unless the change crosses those boundaries.

3. **Real development search**

   From the repository root, run `./scripts/smoke-dev-search.sh`. It health-checks `scheme-processor`, local Firebase Functions, and the real Next.js frontend in dependency order; connects search to `schemessg-v3-dev`; and requires real results through Playwright. This credentialed smoke is separate from secretless PR tests; see `../docs/smoke-testing.md`.

4. **Backend pipeline development**

   Use `backend/docker-compose-firebase.yml` for hands-on `scheme-processor`, trigger, scraping, or Slack development with hot reload. The root smoke also starts `scheme-processor`, but only proves its non-mutating `/health` endpoint before testing search.
5. **Build & Test (Time to shine)**
   Staging:
   ```bash
   npm run build:staging
   npm run test-build:staging
   ```
   Production:
   ```bash
   npm run build:prod
   npm run test-build:prod
   ```
4. **Deploy to Firebase**
   ```bash
   # deploy to production (github action will trigger this)
   export $(cat .env.prod | xargs) && firebase deploy --only hosting:prod --project schemessg
   ```


## Key Scripts

- 🔥 `npm run dev`: Fire up the development server (APP_ENV=development)
- 🏗️ `npm run build:staging`: Construct for staging (APP_ENV=staging)
- 🚀 `npm run build:prod`: Launch-ready for production (APP_ENV=production)
- 🧪 `npm run test-build:staging/prod`: Build and serve locally

## Testing

The fast frontend suite uses Vitest, React Testing Library, and deterministic
MSW handlers. It does not require Firebase or API credentials.

`npm run build` also supports secretless validation. Without Firebase or API
configuration, it creates no Firebase client, makes no deployed API request,
and generates a sitemap containing static routes only. Supply the environment
files when producing an artifact for deployment.

```bash
npm test                  # all unit and integration tests once
npm run test:unit         # unit tests
npm run test:integration  # integrated provider/page tests
npm run test:watch        # watch mode
npm run test:coverage     # coverage report with enforced 70/60 global floors
npm run test:e2e:install  # install the Chromium browser once
npm run test:e2e          # desktop and Pixel 10 Chromium journeys
npm run test:e2e:nightly  # desktop Chromium, Firefox, and WebKit journeys
npm run test:e2e:staging  # read-only smoke against deployed development hosting
npm run test:e2e:update-snapshots # explicitly update reviewed visual baselines
npm run test:e2e:report   # open the latest Playwright HTML report
npm run typecheck         # TypeScript
npm run lint              # ESLint
npm run build             # production build; install dependencies separately
```

The Playwright journey starts a deterministic Next.js development server and
intercepts anonymous Firebase authentication and backend SSE traffic with dummy
credentials and fixture data. All other external browser requests are blocked.
No environment file, deployed service, or production data is used.

On failure, Playwright writes screenshots and local traces to `test-results/`
and an HTML report to `playwright-report/`. CI retries once and captures the
first-retry trace. The scheduled/manual browser workflow uploads these outputs
for seven days when a cross-browser or deployed-staging check fails.

`npm run test:e2e:nightly` uses the same deterministic fixtures as the PR suite
but runs every desktop journey in Chromium, Firefox, and WebKit. Firefox and
WebKit skip screenshot assertions so the reviewed Chromium baselines stay
unchanged. This broader suite runs only on the nightly schedule or manual
dispatch.

`npm run test:e2e:staging` is fixed to
`https://schemessg-v3-dev.web.app`; it accepts no target override, credential,
or secret. The availability/configuration project must pass before the product
project checks the landing and catalog routes. The configuration gate verifies
that deployed bundles point to the development Firebase project and API. The
browser guard aborts every off-origin request and every method other than GET,
HEAD, or OPTIONS, so the smoke cannot write development or production data.

See [ADR 0001](docs/adr/0001-frontend-testing-foundation.md) for the accepted
testing boundaries and deferred work.

## Workflow & Contributing

1. 🌿 Branch out from `stg`
2. ✏️ Make your changes, focusing on `src/app/page.tsx` for main content
3. 🧪 Test locally with `npm run dev`
4. 💾 Commit and push to your branch
5. 🙋 Create a Pull Request to the `stg` branch
6. 👀 After review and approval, your changes will join the party!
7. 🚀 For production, create a PR from `stg` to `main`

## Deployment

- 🚦 **Staging**: Auto-deploys from `stg` branch
- 🚀 **Production**: Auto-deploys from `main` branch

🤖 GitHub Actions is currently configured to automatically deploy changes from the `stg` branch to the schemessg-v3-dev project, and `main` branch to schemessg project. No manual intervention required.

To prepare for future production deployment:
1. 🕵️ Thoroughly investigate on staging
2. 📝 Create a PR from `stg` to `main`
3. 🎉 Once production is set up, merging to `main` will trigger deployment

Note: Production deployment will be configured in the future. Stay tuned for updates!

## Environment

- 🌍 `APP_ENV`: Set to `development`, `staging`, or `production`
- ⚙️ Configure in `next.config.mjs` and set in npm scripts
- Download the environment files (.env.*) from [Google Drive](https://drive.google.com/drive/u/2/folders/1RtqR8vZtjMrgqIGa-uQEZJa9x4dL3z4U) and place them in the frontend root directory before proceeding.

## URLs

- 🧪 Staging: [https://schemessg-v3-dev.web.app/](https://schemessg-v3-dev.web.app/)
- 🚀 Production: [https://schemes.sg](https://schemes.sg)
