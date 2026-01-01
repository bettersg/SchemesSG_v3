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
- **Vector-Based Scheme Matching**: FAISS similarity search to match user situations with the most relevant support schemes
- **Serverless Architecture**: Firebase Cloud Functions with Python runtime for scalable, maintainable backend operations
- **Modern Web Interface**: Responsive Next.js frontend with TypeScript for a seamless user experience

## Prerequisites

Ensure you have the following installed:
- **Node.js** (v14 or later): [Download Node.js](https://nodejs.org/)
- **npm** (v6 or later): Comes with Node.js
- **Python** (v3.10): [Download Python](https://www.python.org/downloads/)
- **Firebase CLI**: Install globally using `npm install -g firebase-tools`
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Included with Docker Desktop

## Key branches
- **main** branch contains frontend and backend code - push to Schemes prod
- **stg** branch contains frontend and backend code - push to Schemes dev
- **telegram_bot** branch contains telegram bot code - push to GCP
- **dataset-workflow** branch contains files to update dataset and do webscraping adhoc
- **v3-archive-021224** contains mix of old and prototype scheemes code for reference

### Required Files Setup

1. **Environment Variables and Model Files**
Download the following required files from Google Drive (contact maintainers for access):
- `.env` file → place in `backend/functions/`
- Required `vector_store/` → place in `backend/functions/ml_logic/`

Note: The `.env` file contains sensitive configuration for Azure OpenAI services and should never be committed to version control.

## Project Structure

The project consists of two main components:

1. **Frontend**: Next.js application with TypeScript
   - See `frontend/README.md` for setup instructions
   - Staging URL: https://schemessg-v3-dev.web.app/
   - Staging URL: https://schemes.sg/

2. **Backend**: Firebase Functions with Python 3.10 runtime
   - See `backend/README.md` for setup instructions
   - Staging URL: https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/
   - Staging URL: https://asia-southeast1-schemessg.cloudfunctions.net/

## Development Workflow

1. Frontend changes:
   - Branch from `stg`
   - Make changes
   - Test locally
   - Create PR to `stg`
   - When PR is merged, github action `.github/workflows/firebase-hosting-staging.yml` will be triggered to deploy to firebase hosting in Schemes dev
   - Then create PR to merge `stg` into `main`
   - When PR is merged, github action `.github/workflows/firebase-hosting-production.yml` will be triggered to deploy to firebase hosting in Schemes prod

2. Backend changes:
   - Test using Firebase emulator
   - When `stg` branch is pushed, the github action `.github/workflows/deploy_functions_dev.yml` will be triggered to deploy to Schemes dev
   - When `main` branch is pushed, the github action `.github/workflows/deploy_functions_prod.yml` will be triggered to deploy to Schemes prod

Note: For local frontend development to work, you must have the backend running via Docker. Please refer to `backend/README.md` for Docker setup and running instructions.

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
