# 🚀 SchemesSG V3 Frontend

Welcome to the Next.js frontend for SchemesSG V3! Let's build something awesome together.

## 📚 Quick Navigation
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Key Scripts](#key-scripts)
- [Workflow & Contributing](#workflow--contributing)
- [Deployment](#deployment)
- [Environment](#environment)
- [URLs](#urls)

## Prerequisites

Before we dive in, make sure you've got:
- 💻 Node.js (v14 or later)
- 📦 npm (v6 or later)
- 🐙 Git

## Quick Start

1. **Setup (Let's get this party started!)**
   ```bash
   cd frontend
   npm install
   ```

   If Errors:
   ```bash
   rm -rf node_modules
   rm package-lock.json
   npm cache clean --force
   npm install
   ```

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


## Key Scripts

- 🔥 `npm run dev`: Fire up the development server (APP_ENV=development)
- 🏗️ `npm run build:staging`: Construct for staging (APP_ENV=staging)
- 🚀 `npm run build:prod`: Launch-ready for production (APP_ENV=production)
- 🧪 `npm run test-build:staging/prod`: Build and serve locally

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
- 🚀 **Production**: Not set up yet

🤖 GitHub Actions is currently configured to automatically deploy changes from the `stg` branch to the staging environment. No manual intervention required for staging deployment!

To prepare for future production deployment:
1. 🕵️ Thoroughly investigate on staging
2. 📝 Create a PR from `stg` to `main`
3. 🎉 Once production is set up, merging to `main` will trigger deployment

Note: Production deployment will be configured in the future. Stay tuned for updates!

## Environment

- 🌍 `APP_ENV`: Set to `development`, `staging`, or `production`
- ⚙️ Configure in `next.config.mjs` and set in npm scripts

## URLs

- 🧪 Staging: [https://schemessg-v3-dev.web.app/](https://schemessg-v3-dev.web.app/)
- 🚀 Production: Not available yet

For more details on the upcoming production setup, reach out to the team lead. Happy coding! 🎉
