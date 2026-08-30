# Schemes Reimagined

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fschemes.sg)](https://schemes.sg)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/node-%3E%3D%2014.0.0-brightgreen)](https://nodejs.org/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/bettersg/SchemesSG_v3/issues)
[![better.sg](https://img.shields.io/badge/Built%20by-better.sg-blue)](https://better.sg)

**Schemesv3** is a modern reimagining of Singapore's social support system search, built using Firebase Cloud Functions and Next.js. The system leverages Azure OpenAI's GPT models to provide intelligent scheme recommendations and natural language interactions.

The core functionality is powered by a sophisticated search system that combines:
- **Natural Language Search**: Users can describe their situation in everyday language and receive relevant scheme recommendations
- **Intelligent Chat Interface**: Contextual conversations powered by Azure OpenAI to help users understand scheme eligibility and application processes
- **Hybrid Search**: Combines BM25 keyword matching with Firestore Vector Search for accurate scheme recommendations
- **Serverless Architecture**: Firebase Cloud Functions with Python runtime for scalable, maintainable backend operations
- **Modern Web Interface**: Responsive Next.js frontend with TypeScript for a seamless user experience

## Prerequisites

Ensure you have the following installed:
- **Node.js** (v20.19 or later): [Download Node.js](https://nodejs.org/)
- **npm**: Comes with Node.js
- **Python** (v3.10–3.12): [Download Python](https://www.python.org/downloads/)
- **uv**: [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Included with Docker Desktop

## Key branches
- **main** branch contains frontend and backend code - push to Schemes prod
- **stg** branch contains frontend and backend code - push to Schemes dev
- **telegram_bot** branch contains telegram bot code - push to GCP
- **dataset-workflow** branch contains files to update dataset and do webscraping adhoc
- **v3-archive-021224** contains mix of old and prototype scheemes code for reference

### Required Files Setup

Download the required ignored configuration from the maintainers:

- `backend/functions/.env` — local Functions and scheme-processor configuration for `schemessg-v3-dev`
- `backend/functions/creds.json` — development Firebase service account
- `frontend/.env.staging` — frontend configuration for `schemessg-v3-dev`
- `.env.dev` / `.env.prod` — deployment-only configuration where documented

These files contain sensitive Firebase, Azure OpenAI, and Slack configuration. Never commit or copy them into task worktrees. The smoke runner locates them in the primary checkout and mounts them read-only.

## Project Structure

| Directory | Description |
|-----------|-------------|
| `frontend/` | Next.js application with TypeScript - see [frontend/README.md](frontend/README.md) |
| `backend/` | Firebase Functions + Cloud Run services - see [backend/README.md](backend/README.md) |
| `backend/functions/` | Firebase Functions (Python 3.10) - API endpoints, triggers, Slack handlers |
| `backend/scheme-processor/` | Cloud Run service (Python 3.11) - web scraping, LLM extraction |
| `backend/scripts/` | Data management scripts - see [backend/scripts/README.md](backend/scripts/README.md) |
| `.github/workflows/` | GitHub Actions for CI/CD deployment |

### URLs

| Environment | Frontend | Backend |
|-------------|----------|---------|
| Production | https://schemes.sg | https://asia-southeast1-schemessg.cloudfunctions.net/ |
| Development | https://schemessg-v3-dev.web.app/ | https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/ |

## Local Development and Verification

Choose the smallest runtime that covers the change:

| Need | Runtime | Command |
|---|---|---|
| Frontend-only development | Next.js on the host; use deterministic tests for API behavior | `cd frontend && npm run dev` |
| Backend pipeline development (Functions, triggers, scraping, Slack, scheme-processor) | Backend development Compose stack | `cd backend && docker compose -f docker-compose-firebase.yml up --build` |
| Real frontend-to-search verification | Root credentialed development smoke against `schemessg-v3-dev` | `./scripts/smoke-dev-search.sh` |

Keep `backend/docker-compose-firebase.yml`: it includes `scheme-processor`, hot reload, and backend ports needed for backend-only work. The root `compose.dev-smoke.yml` is the cross-boundary acceptance stack: it starts `scheme-processor`, waits for its health check, starts Functions, waits for Functions health, starts the frontend, and executes a real browser search against development Firestore. See `docs/smoke-testing.md` for credentials, safety, limitations, and evidence.

Normal changes branch from `stg` and open a PR to `stg`. Merging `stg` deploys the development environment. Production promotion is a separate `stg` → `main` PR; merging `main` deploys production.

## Link Check & Reindex

A scheduled batch job runs monthly (1st of each month at 9am) to:
1. Check all scheme links for dead links
2. Mark dead links as inactive in Firestore
3. Post summary to Slack
4. Reindex Firestore embeddings (excluding inactive schemes)

To trigger manually:

**Option 1: Run locally**
```bash
cd backend/functions
uv run python -c "from batch_jobs.run_link_check_and_reindex import run_link_check_and_reindex_core; run_link_check_and_reindex_core()"
```

**Option 2: Trigger from Google Cloud Console**
1. Go to [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
2. Select the appropriate project (`schemessg-v3-dev` or `schemessg`)
3. Find the job: `firebase-schedule-scheduled_link_check_and_reindex-asia-southeast1`
4. Click **"Run Now"**

## Contributing

We welcome contributions from the community! Here's how you can help:

1. **Report Issues**: Create issues for bugs or feature requests
2. **Submit Pull Requests**: 
   - Fork the repository
   - Create a feature branch from `stg`
   - Make your changes
   - Submit a pull request to `stg`
   - Once approved and merged to `stg`, create another PR to merge into `main`

Please ensure your PR:
- Follows the existing code style
- Includes appropriate tests
- Updates documentation as needed
- Describes the changes made

## Community

- **Website**: [https://schemes.sg](https://schemes.sg)
- **Issues**: Please report bugs and feature requests through GitHub issues
- **Discussions**: Feel free to start discussions in the GitHub Discussions tab
- **Contact**: For other inquiries, reach out to the maintainers through GitHub

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with support from better.sg
- Powered by Azure OpenAI
- Special thanks to all contributors and maintainers
