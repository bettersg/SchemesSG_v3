# SchemesSG Production Restore Status

**Date:** 2026-02-20
**GCP Project:** `schemessg`
**Incident:** Project was deleted ~3 days ago and restored via GCP UI.

---

## Restoration Status

| Component | Status | Notes |
|-----------|--------|-------|
| GCP project restored | ✅ | Project metadata and resources restored |
| Cloud Run services (16) | ✅ | All services intact and running |
| GCS buckets | ✅ | All buckets intact |
| Firestore database | ⚠️ Deleted state | Returns "Cannot serve requests because the database was deleted" — needs re-enable, then data import from CSV backups |
| Firebase Hosting | ❌ Site missing | `schemessg` hosting site returns 404 — needs to be recreated and redeployed |
| `prod-creds.json` key `62c977bbd...` | ✅ | Key is active (no expiry, not disabled) — confirmed via IAM key list |

---

## Firestore Recovery Steps

### Step 1: Re-create the Firestore database (manual)

The database is in a deleted state. Re-create it:

```bash
# Option A: Delete the tombstone and re-create
gcloud --project=schemessg firestore databases delete --database='(default)'
gcloud --project=schemessg firestore databases create --database='(default)' --location=asia-southeast1

# Option B: Check GCP Console → Firestore for an "undelete" option
```

### Step 2: Import data from CSV backups

CSV backup files are in `dataset_workflow/helper_scripts/`:

| Firestore Collection | CSV File | JSON Fields to Parse |
|----------------------|----------|----------------------|
| `schemes` | `firestore-schemes-prod.csv` | _(none)_ |
| `chatHistory` | `firestore-chatHistory-prod.csv` | `messages`, `metadata`, `versions` |
| `schemeEntries` | `firestore-schemeEntries-prod.csv` | _(none)_ |
| `schemes_embeddings` | `firestore-schemes_embeddings-prod.csv` | `embedding` |
| `userFeedback` | `firestore-userFeedback-prod.csv` | _(none)_ |
| `userQuery` | `firestore-userQuery-prod.csv` | `schemes_response` |

Run the import script (after database is re-enabled):

```bash
cd dataset_workflow/helper_scripts
node import-firestore-structure.js
```

The script includes existence checks — it will skip any collection that already has documents.

### Step 3: Verify counts

```bash
node count_documents.js
```

Then check Firestore Console for document counts in each collection.

---

## Firebase Hosting Recovery Steps

The `schemessg` hosting site needs to be recreated:

```bash
# 1. Re-add the hosting site via Firebase Console or CLI
firebase hosting:sites:create schemessg --project=schemessg

# 2. Redeploy
firebase deploy --only hosting --project=schemessg
```

---

## Service Account

- **Account:** `firebase-adminsdk-jt0tt@schemessg.iam.gserviceaccount.com`
- **Key ID:** `62c977bbd56aabd37a001ae7ec25328bb4d55ee1`
- **Status:** Active — no changes needed
- **Credential file:** `dataset_workflow/prod-creds.json`
