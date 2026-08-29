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

2. **Development (Where the magic happens)**
   ```bash
   npm run dev
   ```
   🌐 Access your creation at `http://localhost:3000`

3. **Build & Test (Time to shine)**
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
npm run test:coverage     # coverage report, without enforcement thresholds
npm run test:e2e:install  # install the Chromium browser once
npm run test:e2e          # Chromium landing-to-results browser journey
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
first-retry trace for a future workflow to upload.

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
