# SchemesSG Dataset Workflow

This directory contains scripts for managing the SchemesSG database and model setup.

## Prerequisites

### Firebase Credentials Setup
1. Get Service Account credentials:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as:
     - `dev-creds.json` for development environment
     - `prod-creds.json` for production environment
   - Add these files to `.gitignore`

2. Security Rules:
   - Temporarily allow all operations during import:
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=} {
      allow read, write: if true;
    }
  }
}
```

## Initial Database Setup

### Database Structure Setup
- `export-firestore-structure.js`: Exports the database structure from dev environment
- `import-firestore-structure.js`: Imports the database structure to production
- `schemes-dev-firestore-structure.json`: Database structure definition including:
  - Collections: schemes, chatHistory, schemeEntries, userFeedback, userQuery
  - Field definitions and types
  - Initial schemes data

### Usage

Export structure from dev
`node export-firestore-structure.js`
Import structure to production
`node import-firestore-structure.js`


## Regular Maintenance Workflow

## Regular Maintenance Workflow

### 1. Update Schemes Data
- Update `schemes.csv` with new schemes information
- Fields required:
  - Scheme Name
  - Description
  - Agency
  - Categories
  - Links
  - etc.

### 2. Model Creation
- `model-creation-transformer-laiss.ipynb`
  - Jupyter notebook for creating:
    - Model files for embeddings
    - Faiss index for similarity search
  - Input: Updated schemes.csv
  - Output:
    - model files
    - index files

### 3. Database Update
- `import-csv.js`: Updates schemes collection with new data

### 4. Web Scraping
- `Main_scrape/`: Python scripts for content scraping
  - Uses Beautiful Soup for web scraping
  - Updates `scraped_text` field in Firestore
  - Handles different website structures and error cases

### 5. Model Deployment
1. Zip model files:
2. Upload to Firebase Storage
3. Trigger GitHub Actions to update Firebase Functions

## Utility Scripts

### `count_documents.js`
- Counts documents in Firestore collections



## Files to Remove/Archive
The following files are no longer relevant to the workflow:
1. `old-import-scripts/`: Legacy import scripts
2. `test-data/`: Old test datasets
3. Any CSV files other than the current `schemes.csv`

## Important Notes
- Always test changes in dev environment first
- Backup data before major updates
- Check Firebase quotas before large operations
- Verify security rules after structure changes
- Keep credentials secure and never commit them to git
- After import, update security rules to production settings

## Troubleshooting
Common issues and solutions:
1. Firestore permissions errors:
   - Verify credentials JSON is correct
   - Check security rules
2. Import failures:
   - Ensure database exists in Firebase Console
   - Verify database name in import script
3. Model creation issues:
   - Check Python dependencies
   - Verify input CSV format

## Directory Structure
```
dataset_workflow/
├── credentials/ # Store credentials here (gitignored)
│ ├── dev-creds.json
│ └── prod-creds.json
├── scripts/
│ ├── export-firestore-structure.js
│ ├── import-firestore-structure.js
│ └── import-csv.js
├── data/
│ └── schemes.csv # Current schemes data
├── models/ # Generated model files
└── Main_scrape/ # Web scraping scripts
```
