# SchemesSG v3 Backend - Developer Guide for AI Assistants

This document contains critical information about the SchemesSG backend architecture, environment configuration, and common gotchas. Read this carefully before making changes.

## Project Overview

SchemesSG is a Singapore government schemes discovery platform. The backend uses:
- **Firebase Firestore**: Database for scheme data and vector search (native Firestore Vector Search)
- **Firebase Functions**: Cloud functions for API and integrations
- **Slack Integration**: Admin approval workflow for new scheme submissions
- **crawl4ai**: Web scraping and LLM extraction for new schemes

## Critical: Two Dependency Files

The project has **two separate dependency files** for different purposes:

### `pyproject.toml` (Root backend/)
- **Purpose**: Local development with `uv` package manager
- **Used for**: Running scripts locally, running tests, local development
- **Commands**: `uv run python scripts/...`, `uv run pytest`, `uv sync`
- **Managed by**: uv (creates `.venv/` directory)

### `functions/requirements.txt`
- **Purpose**: Firebase Functions deployment
- **Used for**: Cloud deployment of Firebase Functions
- **Commands**: `firebase deploy --only functions`
- **Note**: Firebase reads this file during deployment to install dependencies

### ⚠️ IMPORTANT: Keep Dependencies in Sync
When adding a new dependency:
1. Add to `functions/requirements.txt` (for Firebase deployment)
2. Add to `pyproject.toml` (for local development/testing)
3. Run `uv sync` to update local environment

**Example**:
```bash
# After adding a new package
echo "new-package==1.0.0" >> functions/requirements.txt
# Then add same version to pyproject.toml dependencies array
uv sync
```

## Critical: Two Firebase Projects

This is the most important thing to understand:

### Production Project
- **Project ID**: `schemessg`
- **Database**: Real production data with actual emails, phone numbers
- **Credentials**: `functions/.env.prod`
- **Use for**: Downloading production data only

### Development Project
- **Project ID**: `schemessg-v3-dev`
- **Database**: Test/development data (may contain anonymized data)
- **Credentials**: `functions/.env`
- **Use for**: Local emulator, development, testing

### ⚠️ CRITICAL GOTCHA: Project ID Conflicts

**Problem**: Firestore emulator runs in "single project mode" by default. If you try to import data from production (project: `schemessg`) into an emulator running as `schemessg-v3-dev`, the data will be stored but **not visible in the UI**.

**Symptom**: API shows data exists, but Firestore Emulator UI (http://localhost:4000) shows no documents.

**Solution**: Use the download → load workflow (see "Production Data Replication" section below).

## Environment Variables & Secrets

### Files

```
functions/
├── .env              # Local development (uses local scheme-processor)
├── .env.dev          # Dev deployment credentials (project: schemessg-v3-dev)
└── .env.prod         # Prod deployment credentials (project: schemessg)
```

### Environment File Structure

All env files contain the same Firebase credential fields (with different values):

```bash
# Firebase Admin SDK credentials
FB_TYPE=service_account
FB_PROJECT_ID=schemessg-v3-dev  # or 'schemessg' for .env.prod
FB_PRIVATE_KEY_ID=xxxxx
FB_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FB_CLIENT_EMAIL=firebase-adminsdk-xxxxx@schemessg-v3-dev.iam.gserviceaccount.com
FB_CLIENT_ID=xxxxx
FB_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FB_TOKEN_URI=https://oauth2.googleapis.com/token
FB_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FB_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/xxxxx
FB_UNIVERSE_DOMAIN=googleapis.com

# Other services
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=xxxxx
OPENAI_API_KEY=sk-xxxxx
```

### Important Notes

1. **`FB_PRIVATE_KEY` formatting**:
   - Stored with escaped newlines: `\\n`
   - Python code must replace: `os.getenv("FB_PRIVATE_KEY").replace("\\n", "\n")`
   - This is done in all scripts and `FirebaseManager`

2. **Which env file to use**:
   - Local Docker development: Uses `.env` (local scheme-processor URL)
   - Scripts with `--dev` flag: Use `.env.dev`
   - Scripts with `--prod` flag: Use `.env.prod`
   - GitHub Actions: Uses `.env.dev` or `.env.prod` from secrets

3. **Never commit**:
   - `.env`, `.env.dev`, `.env.prod` are in `.gitignore`
   - `prod_schemes_data.json` is in `.gitignore`

## Firestore Emulator Setup

### Docker Configuration

**File**: `docker-compose-firebase.yml`

```yaml
services:
  backend:
    build: .
    ports:
      - "8080:8080"  # Firestore API
      - "4000:4000"  # Firestore UI
      - "5001:5001"  # Functions
    volumes:
      - ./functions:/app/functions
      - ./firestore-backup:/app/firestore-backup
      - ./scripts:/app/scripts
    environment:
      - FIRESTORE_EMULATOR_HOST=localhost:8080
```

### Emulator Startup Script

**File**: `start.sh`

```bash
# Checks for data to import (in priority order)
if [ -d "/app/firestore-backup/current" ]; then
    IMPORT_PATH="/app/firestore-backup/current"  # Data from previous run
elif [ -d "/app/firestore-backup/latest" ]; then
    IMPORT_PATH="/app/firestore-backup/latest"   # Manual import
else
    IMPORT_PATH=""  # Start empty
fi

# Start emulator with project ID (MUST match .env)
firebase emulators:start --only functions,firestore \
    --project schemessg-v3-dev \  # Must match FB_PROJECT_ID in .env
    --debug \
    $IMPORT_FLAG \
    --export-on-exit=/app/firestore-backup/current
```

### Key Configuration Points

1. **Project ID**: Must be `schemessg-v3-dev` (matches `.env`)
2. **Import path**: Checks `/current` first (exported from previous run)
3. **Export on exit**: Saves to `/current` when container stops
4. **Persistence**: Data persists across restarts via `firestore-backup/current/`

### Accessing the Emulator

- **Firestore UI**: http://localhost:4000 (browse data visually)
- **Firestore API**: http://localhost:8080 (programmatic access)
- **Functions**: http://localhost:5001

### Emulator Gotchas

1. **UI shows no data but API returns data**:
   - Cause: Project ID mismatch (data written to different project namespace)
   - Fix: Use download → load workflow, ensure consistent project IDs

2. **Data disappears after restart**:
   - Cause: `--export-on-exit` not working or `firestore-backup/current/` was deleted
   - Fix: Check Docker logs, verify volume mount in docker-compose.yml

3. **Connection refused on localhost:8080**:
   - Cause: Emulator not fully started yet
   - Fix: Wait 10 seconds after `docker compose up`, check `docker logs`

## Production Data Replication Workflow

**Problem**: Cannot directly import from production due to project ID mismatch.

**Solution**: Three-step workflow using local JSON file as intermediary.

### Step 1: Download from Production

```bash
uv run python scripts/download_prod_data.py
```

- Connects to production Firestore (project: `schemessg`)
- Downloads all 480+ schemes
- Saves to `prod_schemes_data.json` with timestamps converted to strings
- Uses: `functions/.env.prod`

### Step 2: Load into Emulator

```bash
docker compose -f docker-compose-firebase.yml up -d
sleep 10  # Wait for emulator startup
uv run python scripts/load_local_data.py
```

- Reads from local `prod_schemes_data.json`
- Connects to emulator (project: `schemessg-v3-dev`)
- Imports all documents into `schemes` collection
- Uses: `functions/.env`

### Why This Approach?

1. **Avoids project ID conflicts**: Local file acts as neutral intermediary
2. **No Cloud SDK required**: Direct Firestore API access
3. **Predictable**: Same credentials used consistently at each step
4. **Debuggable**: Can inspect `prod_schemes_data.json` if issues arise

## Firebase Admin SDK Initialization

### Pattern Used Throughout Codebase

**File**: `functions/fb_manager/firebaseManager.py`

```python
class FirebaseManager:
    """Singleton for Firebase Admin SDK"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FirebaseManager, cls).__new__(cls)
                cls._instance._initialize_app()
            return cls._instance

    def _initialize_app(self):
        if not firebase_admin._apps:
            private_key = os.getenv("FB_PRIVATE_KEY").replace("\\n", "\n")
            cred = credentials.Certificate({
                "type": os.getenv("FB_TYPE"),
                "project_id": os.getenv("FB_PROJECT_ID"),
                # ... other fields
                "private_key": private_key,
            })
            initialize_app(cred)

        self.firestore_client = firestore.client()
```

### Scripts Pattern

Scripts use named apps to avoid conflicts:

```python
# For production connection
try:
    prod_app = firebase_admin.get_app("production")
except ValueError:
    cred = credentials.Certificate({...})
    prod_app = firebase_admin.initialize_app(cred, name="production")

# For emulator connection
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
try:
    emulator_app = firebase_admin.get_app("emulator")
except ValueError:
    cred = credentials.Certificate({...})
    emulator_app = firebase_admin.initialize_app(cred, name="emulator")
```

## Data Schema Gotchas

### Timestamp Fields

**Problem**: Firestore timestamps serialize as `{'_seconds': 1234567890, '_nanoseconds': 123456789}`

**Solution**: Custom formatter in export script:

```python
def format_timestamp(timestamp_value) -> str:
    if isinstance(timestamp_value, dict) and '_seconds' in timestamp_value:
        unix_timestamp = timestamp_value['_seconds']
        dt = datetime.fromtimestamp(unix_timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    # ... handle other formats
```

### List Fields

**Fields**: `phone`, `email`, `address`, `planning_area`, `service_area`

**Handling**: Convert to comma-separated strings when needed:

```python
phone = scheme.get('phone', '')
if isinstance(phone, list):
    phone = ', '.join(phone) if phone else ''
```

## Common Tasks

### Starting Fresh Development Session

```bash
# 1. Start emulator (auto-imports from previous session)
docker compose -f docker-compose-firebase.yml up -d

# 2. Wait for startup
sleep 10

# 3. Verify data exists
curl http://localhost:8080/v1/projects/schemessg-v3-dev/databases/(default)/documents/schemes | grep "documents"

# 4. Open UI to browse
open http://localhost:4000
```

### Refreshing Production Data

```bash
# 1. Download latest from production
uv run python scripts/download_prod_data.py

# 2. Restart emulator fresh
docker compose -f docker-compose-firebase.yml down
docker compose -f docker-compose-firebase.yml up -d
sleep 10

# 3. Load production data
uv run python scripts/load_local_data.py
```

### Debugging Emulator Issues

```bash
# Check if emulator is running
docker compose -f docker-compose-firebase.yml ps

# View emulator logs
docker compose -f docker-compose-firebase.yml logs backend | tail -50

# Check for project ID mismatches
docker compose -f docker-compose-firebase.yml logs backend | grep -i "project"

# Verify data via API (bypasses UI issues)
curl http://localhost:8080/v1/projects/schemessg-v3-dev/databases/(default)/documents/schemes?pageSize=1
```

### Clearing Emulator Data

```bash
# Stop and remove everything
docker compose -f docker-compose-firebase.yml down -v

# Remove backup data
rm -rf firestore-backup/current

# Start fresh
docker compose -f docker-compose-firebase.yml up -d
```

## Project Structure

```
backend/
├── pyproject.toml              # Local dev dependencies (uv) - for scripts & tests
├── functions/
│   ├── requirements.txt        # Firebase Functions dependencies (for deployment)
│   ├── .env                    # Dev credentials (schemessg-v3-dev)
│   ├── .env.prod               # Prod credentials (schemessg)
│   ├── fb_manager/
│   │   └── firebaseManager.py  # Singleton Firebase initialization
│   ├── slack_integration/      # Slack approval workflow
│   │   ├── slack.py            # Main Slack handlers
│   │   ├── block_kit.py        # Slack Block Kit builders
│   │   └── storage.py          # Firestore operations
│   ├── new_scheme/             # New scheme submission pipeline
│   │   ├── trigger_new_scheme_pipeline.py  # Firestore trigger
│   │   ├── pipeline_runner.py  # crawl4ai processing
│   │   ├── new_scheme_blocks.py # Slack message builders
│   │   ├── approval_handler.py # Approval/rejection logic
│   │   └── url_utils.py        # Domain/duplicate checking
│   └── main.py                 # Firebase Functions entry
├── scripts/
│   ├── download_prod_data.py   # Download from production
│   ├── load_local_data.py      # Load into emulator
│   └── README.md               # Detailed script docs
├── tests/                      # Test suite (run with: uv run pytest)
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── firestore-backup/
│   └── current/                # Auto-exported emulator data
├── prod_schemes_data.json      # Downloaded production data (gitignored)
├── docker-compose-firebase.yml # Emulator orchestration
├── start.sh                    # Emulator startup script
└── CLAUDE.md                   # This file
```

## Security Checklist

Before committing code, verify:

- [ ] No `.env` or `.env.prod` files committed
- [ ] No `prod_schemes_data.json` committed
- [ ] No `firestore-backup/` directory committed (except `.gitkeep`)
- [ ] No hardcoded credentials in code
- [ ] All credential references use `os.getenv()`
- [ ] Private keys processed with `.replace("\\n", "\n")`

## Troubleshooting Decision Tree

### Emulator UI shows no data

1. **Check if data exists via API**:
   ```bash
   curl http://localhost:8080/v1/projects/schemessg-v3-dev/databases/(default)/documents/schemes
   ```

2. **If API shows data**:
   - Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
   - Check for project ID mismatch in Docker logs

3. **If API shows no data**:
   - Verify emulator is running: `docker compose ps`
   - Check if data was loaded: `ls firestore-backup/current/`
   - Re-run load script: `uv run python scripts/load_local_data.py`

### "Multiple projectIds not recommended" error

This means project ID mismatch:
- Check `start.sh` line 26: Must be `--project schemessg-v3-dev`
- Check scripts use correct `.env` file for target environment
- Use download → load workflow instead of direct import

## New Scheme Submission Pipeline

### Overview

When anonymous users submit new schemes via the public form, the pipeline:
1. Firestore trigger (`on_new_scheme_entry`) fires on `schemeEntries/{docId}` creation
2. Checks for duplicate domains in existing `schemes` collection
3. Runs crawl4ai to scrape and extract structured data (LLM fields)
4. Extracts logo using scoring algorithm (prioritizes header/footer images)
5. Posts to Slack for human review with "Review & Approve" / "Reject" buttons
6. Admin reviews in Slack modal, can edit fields before approval
7. Approved schemes are added to `schemes` collection

### Key Files

- `functions/new_scheme/trigger_new_scheme_pipeline.py` - Firestore trigger
- `functions/new_scheme/pipeline_runner.py` - crawl4ai processing, logo extraction
- `functions/new_scheme/new_scheme_blocks.py` - Slack Block Kit builders
- `functions/new_scheme/approval_handler.py` - Handles approval/rejection
- `functions/new_scheme/url_utils.py` - Domain extraction, duplicate checking

### Logo Extraction Algorithm

Scores images from crawl4ai based on:
- **+20 points**: URL/alt contains "logo", "brand", "icon", "emblem"
- **+15 points**: URL/alt/desc contains "header", "nav", "footer", "masthead"
- **+10 points**: SVG format (common for logos)
- **+3 points**: PNG format
- **-25 points**: Contains "banner", "hero", "social", "facebook", etc.

Relative URLs are converted to absolute using `urljoin(base_url, src)`.

### Slack Integration Gotchas

1. **Image preview errors**: Slack validates image URLs - must be absolute and accessible
2. **URL unfurling**: Disable with `unfurl_links: False, unfurl_media: False`
3. **Multi-select fields**: Use `multi_static_select` with `initial_options` array
4. **Anonymous submissions**: Don't display user info from `schemeEntries` (may be test data)

### Testing the Pipeline

```bash
# Start emulator
docker compose -f docker-compose-firebase.yml up -d

# Create test entry in schemeEntries collection via Firestore UI
# Or use curl to trigger the HTTP function for testing
```

## Key Takeaways for AI Assistants

1. **Two projects, two purposes**: Production for data, Dev for testing
2. **Never mix project IDs**: Use download → load workflow
3. **Private key formatting**: Always `.replace("\\n", "\n")`
4. **Named Firebase apps**: Avoid app conflicts in scripts
5. **Emulator persistence**: Data saves to `firestore-backup/current/`
6. **Timestamp handling**: Custom formatter for date display
7. **List field handling**: Convert to comma-separated strings
8. **Security first**: Never commit credentials or production data
9. **Git commits**: Always one-liner (`git add <files> && git commit -m "message"`), NO Claude signature

## Git Commit Best Practices

**Always use one-liner format without Claude signature:**

```bash
git add <files> && git commit -m "Add feature description"
```

**Commit message rules:**
- Use imperative mood ("Add", "Fix", "Update", not "Added", "Fixed")
- Subject line under 50 characters
- No period at end of subject
- NO Claude/AI signatures or co-author lines

**Examples:**
```bash
git add functions/new_scheme/ && git commit -m "Add new scheme submission pipeline"
git add .gitignore && git commit -m "Add credentials to gitignore"
git add functions/slack_integration/slack.py && git commit -m "Fix Slack modal image preview"
```

## When Making Changes

1. **Environment changes**: Update both `.env.example` and this doc
2. **Script changes**: Update `scripts/README.md` docstrings
3. **Schema changes**: Update normalization mappings if needed
4. **Docker changes**: Test full restart cycle with data persistence
5. **New secrets**: Add to `.gitignore` immediately

## Need Help?

- **Scripts documentation**: `scripts/README.md`
- **Docker logs**: `docker compose -f docker-compose-firebase.yml logs`
- **Emulator UI**: http://localhost:4000
- **Test API**: `curl http://localhost:8080/v1/projects/schemessg-v3-dev/databases/(default)/documents/schemes`

---

*Last updated: 2026-01-01*
*Reflects learnings from new scheme pipeline implementation*
