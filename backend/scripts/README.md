# Scripts Documentation

This document covers all utility scripts for the SchemesSG backend.

## Quick Reference

| Script | Location | Purpose | When to Use |
|--------|----------|---------|-------------|
| `populate_embeddings.py` | `functions/scripts/` | Initial vector embeddings setup | **One-time** per environment |
| `test_vector_search.py` | `functions/scripts/` | Test vector search queries | Development/debugging |
| `run_link_check_and_reindex.py` | `functions/scripts/` | Manual link check + reindex | Ad-hoc maintenance |
| `download_prod_data.py` | `scripts/` | Download production data | Refresh local data |
| `download_dev_data.py` | `scripts/` | Download dev data | Refresh local data |
| `load_local_data.py` | `scripts/` | Load data into emulator | After download |
| `normalize_and_export_to_sheets.py` | `scripts/` | Export to Google Sheets | Admin review workflow |

---

## Vector Search & Embeddings

SchemesSG uses Firestore Vector Search for semantic search. The `schemes_embeddings` collection stores embeddings (2048-dim vectors from Azure OpenAI `text-embedding-3-large`).

### Initial Setup (One-Time)

**Script:** `functions/scripts/populate_embeddings.py`

Run this **once** to create the initial embeddings for a new environment:

```bash
cd backend/functions

# For dev environment (schemessg-v3-dev)
uv run python scripts/populate_embeddings.py --dev

# For production environment (schemessg)
uv run python scripts/populate_embeddings.py --prod
```

**Important:**
- Requires explicit `--dev` or `--prod` flag (no default)
- Production requires typing "yes" to confirm
- Only run once per environment - use reindex for updates

**Prerequisites:**
- `.env.dev` (dev) or `.env.prod` (production) with Firebase + Azure OpenAI credentials
- Vector index deployed: `firebase deploy --only firestore:indexes --project <project-id>`

### Ongoing Maintenance (Automated)

**Scheduled Function:** `scheduled_link_check_and_reindex`

Runs automatically on the **1st of every month at 9am SGT**. This function:
1. Checks all scheme links for dead URLs
2. Marks dead links as `status='inactive'`
3. Restores previously inactive schemes if links are alive again
4. Reindexes embeddings (excluding inactive schemes)
5. Posts summary to Slack

No manual intervention needed - just ensure the function is deployed.

### Manual Reindex (Ad-Hoc)

**Script:** `functions/scripts/run_link_check_and_reindex.py`

For manual link checking and reindexing outside the monthly schedule:

```bash
cd backend/functions
uv run python scripts/run_link_check_and_reindex.py
```

Or via Python:
```bash
uv run python -c "from batch_jobs.run_link_check_and_reindex import run_link_check_and_reindex_core; run_link_check_and_reindex_core()"
```

### Testing Vector Search

**Script:** `functions/scripts/test_vector_search.py`

Test vector search queries against the embeddings collection:

```bash
cd backend/functions
uv run python scripts/test_vector_search.py
```

---

## Data Management

### Production Data Replication Workflow

Three-step process to work with production data locally:

```
download_prod_data.py → load_local_data.py → normalize_and_export_to_sheets.py
```

**Why this approach:**
- Avoids project ID conflicts (prod: `schemessg`, dev: `schemessg-v3-dev`)
- No Google Cloud SDK required
- Works directly with Firestore API

### Step 1: Download Production Data

**Script:** `download_prod_data.py`

```bash
uv run python scripts/download_prod_data.py
```

- Connects to production Firestore (`schemessg`)
- Downloads all schemes to `prod_schemes_data.json`
- Uses `functions/.env.prod` credentials

### Step 2: Load into Emulator

**Script:** `load_local_data.py`

```bash
# Start emulator first
docker compose -f docker-compose-firebase.yml up -d
sleep 10

# Load data
uv run python scripts/load_local_data.py
```

- Reads `prod_schemes_data.json`
- Loads into emulator at localhost:8080
- Uses `functions/.env` credentials

### Step 3: Export to Google Sheets

**Script:** `normalize_and_export_to_sheets.py`

```bash
uv run python scripts/normalize_and_export_to_sheets.py
```

- Normalizes categories (`who_is_it_for`, `what_it_gives`, `scheme_type`)
- Exports to Google Sheets for admin review
- Requires `functions/google_sheets_credentials.json`

---

## Complete Workflows

### Initial Environment Setup

```bash
# 1. Deploy vector index
firebase deploy --only firestore:indexes --project schemessg-v3-dev  # or schemessg

# 2. Populate embeddings (one-time)
cd backend/functions
uv run python scripts/populate_embeddings.py --dev  # or --prod

# 3. Test vector search
uv run python scripts/test_vector_search.py
```

### Local Development

```bash
# 1. Start emulator (auto-imports from previous session)
docker compose -f docker-compose-firebase.yml up -d

# 2. Develop and test
# ...

# 3. Export to Google Sheets when ready
uv run python scripts/normalize_and_export_to_sheets.py
```

### Refresh Local Data

```bash
uv run python scripts/download_prod_data.py
uv run python scripts/load_local_data.py
```

---

## Directory Structure

```
backend/
├── scripts/                          # Data management scripts
│   ├── README.md                     # This file
│   ├── download_prod_data.py         # Download from production
│   ├── download_dev_data.py          # Download from dev
│   ├── load_local_data.py            # Load into emulator
│   └── normalize_and_export_to_sheets.py
│
├── functions/
│   ├── scripts/                      # Vector search scripts
│   │   ├── populate_embeddings.py    # One-time embedding setup
│   │   ├── test_vector_search.py     # Test queries
│   │   └── run_link_check_and_reindex.py  # Manual reindex
│   │
│   ├── batch_jobs/                   # Scheduled functions
│   │   └── run_link_check_and_reindex.py  # Monthly scheduled job
│   │
│   ├── .env                          # Dev credentials
│   └── .env.prod                     # Production credentials
│
├── firestore-backup/
│   └── current/                      # Emulator auto-export
│
├── prod_schemes_data.json            # Downloaded data (gitignored)
└── docker-compose-firebase.yml
```

---

## File Descriptions

| File | Purpose | Credentials |
|------|---------|-------------|
| `scripts/download_prod_data.py` | Download from production Firestore | `.env.prod` |
| `scripts/download_dev_data.py` | Download from dev Firestore | `.env.dev` |
| `scripts/load_local_data.py` | Load JSON into emulator | `.env` |
| `scripts/normalize_and_export_to_sheets.py` | Export to Google Sheets | `.env` + Sheets API |
| `functions/scripts/populate_embeddings.py` | One-time embedding population | `.env.dev` or `.env.prod` |
| `functions/scripts/test_vector_search.py` | Test vector search | `.env` |
| `functions/scripts/run_link_check_and_reindex.py` | Manual link check + reindex | `.env` |

---

## Troubleshooting

### Vector search returns no results
1. Check embeddings exist: Query `schemes_embeddings` collection in Firebase Console
2. Verify index is deployed: `firebase deploy --only firestore:indexes`
3. Run `test_vector_search.py` to debug

### Emulator shows no data
```bash
docker compose -f docker-compose-firebase.yml ps
curl http://localhost:8080/v1/projects/schemessg-v3-dev/databases/(default)/documents/schemes
```

### Project ID mismatch errors
Use the download → load workflow. Never directly import between projects.

---

## Security Notes

**Never commit:**
- `.env` / `.env.prod`
- `prod_schemes_data.json`
- `firestore-backup/`
- `google_sheets_credentials.json`

All are in `.gitignore`.
