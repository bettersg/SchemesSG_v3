# Backend for SchemesSG V3

Backend services for the Singapore government schemes discovery platform.

## Quick Navigation
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [scheme-processor (Cloud Run)](#scheme-processor-cloud-run)
- [New Scheme Flow](#new-scheme-flow)
- [Batch Jobs](#batch-jobs)
- [Scripts](#scripts)
- [Deployment](#deployment)
- [Firebase Projects](#firebase-projects)

## Architecture

The backend consists of two main components:

1. **Firebase Functions** (Python 3.10) - API endpoints, Slack handlers, Firestore triggers
2. **scheme-processor** (Cloud Run, Python 3.11) - Heavy processing: web scraping, LLM extraction

### Tech Stack
- **Database**: Firestore with native Vector Search
- **Search**: Firestore Vector Search (migrated from ChromaDB)
- **LLM**: Azure OpenAI for field extraction
- **Scraping**: crawl4ai (primary) + pydoll (Cloudflare bypass)
- **Admin Workflow**: Slack approval for new schemes

### New Scheme Submission Flow
```
User submits scheme (/contribute)
         │
         ▼
  Creates doc in schemeEntries
         │
         ▼
  Firestore trigger fires
         │
         ▼
  Calls scheme-processor (Cloud Run)
         │
         ▼
  Scrape → LLM Extract → Post to Slack
         │
         ▼
  Admin reviews in Slack modal
         │
         ▼
  Approve → Added to schemes collection
```

### Monthly Batch Job
- Checks all scheme links for validity
- Marks dead links as inactive
- Posts summary to Slack
- Reindexes embeddings into Firestore

## Project Structure

| Directory | Description |
|-----------|-------------|
| `functions/` | Firebase Functions (Python 3.10) - API endpoints, Firestore triggers, Slack handlers |
| `functions/batch_jobs/` | Scheduled jobs (monthly link check & embedding reindex) |
| `functions/ml_logic/` | Search model using Firestore Vector Search |
| `functions/new_scheme/` | Firestore trigger + Slack approval workflow for new submissions |
| `functions/scripts/` | Setup scripts (populate embeddings, test vector search) |
| `functions/.env` | Local development (uses local scheme-processor) |
| `functions/.env.dev` | Dev deployment credentials (`schemessg-v3-dev`) |
| `functions/.env.prod` | Prod deployment credentials (`schemessg`) |
| `scheme-processor/` | Cloud Run service (Python 3.11) - web scraping, LLM extraction |
| `scripts/` | Data management scripts - see [scripts/README.md](scripts/README.md) |
| `firestore.indexes.json` | Firestore indexes including vector search index |

### Directory Tree

```
backend/
├── functions/                   # Firebase Functions (Python 3.10)
│   ├── batch_jobs/              # Scheduled link check and reindex
│   ├── ml_logic/                # Search model (Firestore Vector Search)
│   ├── new_scheme/              # Firestore trigger + Slack approval
│   ├── scripts/                 # Setup scripts (embeddings, testing)
│   ├── .env                     # Dev credentials (schemessg-v3-dev)
│   ├── .env.prod                # Prod credentials (schemessg)
│   └── main.py                  # Functions entry point
├── scheme-processor/            # Cloud Run service (Python 3.11)
│   ├── app/                     # FastAPI application
│   ├── deploy.sh                # Deployment script (--dev/--prod)
│   └── Dockerfile
├── scripts/                     # Data management scripts
│   └── README.md                # Detailed script documentation
├── firestore.indexes.json       # Vector search index config
└── docker-compose-firebase.yml  # Local development
```

## Getting Started

### Prerequisites
- Docker
- uv (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Environment Setup

1. Get credentials from project maintainers:
   ```bash
   # Required files
   functions/.env              # Dev credentials
   functions/creds.json        # Firebase service account
   ```

2. Copy example and fill in values:
   ```bash
   cp functions/.env.example functions/.env
   ```

### Local Development

```bash
# Start all services (Functions + scheme-processor)
docker compose -f docker-compose-firebase.yml up --build

# Access points:
# - Firebase Functions: http://localhost:5001
# - Firestore UI: http://localhost:4000
# - scheme-processor: http://localhost:8081

# Stop services
docker compose -f docker-compose-firebase.yml down

# View logs
docker compose -f docker-compose-firebase.yml logs -f

# Attach to container shell
docker exec -it backend-backend-1 /bin/bash
```

### Loading Production Data (Optional)

To work with real scheme data locally:

```bash
# 1. Download from production
uv run python scripts/download_prod_data.py

# 2. Load into emulator (start Docker first)
uv run python scripts/load_local_data.py
```

## API Endpoints

Base URL (local): `http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/schemes_search` | POST | Search schemes with vector search |
| `/schemes/{id}` | GET | Get scheme by ID |
| `/chat_message` | POST | Chat interface for recommendations |
| `/update_scheme` | POST | Submit new scheme or request edit |
| `/feedback` | POST | Submit user feedback |
| `/retrieve_search_queries/{session_id}` | GET | Get search history |
| `/slack_trigger_message` | POST | Trigger Slack review message |
| `/slack_interactive` | POST | Handle Slack buttons/modals |
| `/keep_endpoints_warm-0` | GET | Warmup function (scheduled) |

### Warmup Requests
All endpoints support warmup to reduce cold starts:
- **GET**: Add `?is_warmup=true`
- **POST**: Include `{"is_warmup": true}` in body

## scheme-processor (Cloud Run)

Separate service for heavy processing tasks.

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/process` | POST | Process new scheme submission |

### Dual Crawler Strategy
1. **crawl4ai** (Primary): BFS deep crawl
   - `max_depth=1`: Crawls 1 level deep
   - `max_pages=5`: Max 5 pages per scheme
   - Aggregates content from multiple pages

2. **pydoll** (Fallback): Cloudflare bypass
   - Headless Chrome with Xvfb virtual display
   - Used when crawl4ai fails on protected sites

### Local Testing
```bash
# Health check
curl http://localhost:8081/health

# Process a scheme (requires valid Firestore doc)
curl -X POST http://localhost:8081/process \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "test", "scheme_name": "Test", "scheme_url": "https://example.com"}'
```

## New Scheme Flow

1. User submits scheme via `/contribute` page
2. Frontend calls `update_scheme` endpoint
3. Creates document in `schemeEntries` collection
4. Firestore trigger (`on_new_scheme_entry`) fires
5. Trigger calls scheme-processor Cloud Run service
6. scheme-processor:
   - Scrapes URL with crawl4ai/pydoll
   - Extracts fields with Azure OpenAI LLM
   - Extracts contacts with regex
   - Gets planning area from OneMap API
   - Updates Firestore with results
   - Posts to Slack for review
7. Admin reviews in Slack modal (can edit fields)
8. On approval: scheme added to `schemes` collection
9. On rejection: entry marked as rejected

## Batch Jobs

### scheduled_link_check_and_reindex
**Schedule**: Monthly (1st of month, 2am SGT)

**What it does**:
1. Checks all scheme links for HTTP 200
2. Marks dead links as `status: "inactive"`
3. Posts summary to Slack with dead links list
4. Regenerates embeddings for active schemes
5. Reindexes into Firestore Vector Search

**Manual trigger**:
```bash
cd backend/functions
uv run python -m scripts.run_link_check_and_reindex
```

## Scripts

For detailed documentation on all scripts, see [scripts/README.md](scripts/README.md).

**Key scripts:**
| Script | Purpose |
|--------|---------|
| `functions/scripts/populate_embeddings.py` | One-time vector embeddings setup (requires `--dev` or `--prod`) |
| `functions/scripts/test_vector_search.py` | Test vector search queries |
| `scripts/download_prod_data.py` | Download production data for local development |

## Deployment

### Firebase Functions
Deployment is handled by GitHub Actions. **Do not use `firebase deploy` manually**.

### scheme-processor (Cloud Run)
```bash
cd backend/scheme-processor

# Deploy to development
./deploy.sh dev

# Deploy to production
./deploy.sh prod
```

The deploy script:
1. Builds container from source
2. Deploys to Cloud Run
3. Sets up IAM permissions for Firebase Functions to call it

## Firebase Projects

**Important**: Two separate Firebase projects exist.

| Environment | Project ID | Purpose |
|-------------|------------|---------|
| Production | `schemessg` | Live data, real users |
| Development | `schemessg-v3-dev` | Testing, emulator |

### Credential Files
- `functions/.env` - Local development (uses local scheme-processor)
- `functions/.env.dev` - Dev deployment (GitHub Actions → `schemessg-v3-dev`)
- `functions/.env.prod` - Prod deployment (GitHub Actions → `schemessg`)
- `functions/creds.json` - Dev service account
- `functions/creds.prod.json` - Prod service account

> **Important**: Scripts like `populate_embeddings.py` and `deploy.sh` require explicit environment flags (`--dev` or `--prod`) to prevent accidental operations on the wrong project.

**Never mix credentials between environments.**

## Security Notes

### Gitignored Files (Never Commit)
- `functions/.env`, `functions/.env.prod`
- `functions/creds.json`, `functions/creds.prod.json`
- `functions/google_sheets_credentials.json`
- `prod_schemes_data.json`
- `firestore-backup/`

### Environment Variables
See `functions/.env.example` for required variables:
- Firebase Admin SDK credentials (`FB_*`)
- Azure OpenAI credentials
- Slack tokens (bot token, signing secret)

## Troubleshooting

### Docker Issues
```bash
# Check if services are running
docker compose -f docker-compose-firebase.yml ps

# View logs
docker compose -f docker-compose-firebase.yml logs backend
docker compose -f docker-compose-firebase.yml logs scheme-processor

# Rebuild from scratch
docker compose -f docker-compose-firebase.yml down -v
docker compose -f docker-compose-firebase.yml up --build
```

### Emulator Shows No Data
The emulator connects to cloud Firestore by default (for vector search support). To see data:
1. Use the production data loading workflow (see [Loading Production Data](#loading-production-data-optional))
2. Or create test data via the Functions API

### scheme-processor Connection Issues
- Ensure both services are running: `docker compose ps`
- Check logs: `docker compose logs scheme-processor`
- Verify `PROCESSOR_SERVICE_URL=http://scheme-processor:8081` in docker-compose
