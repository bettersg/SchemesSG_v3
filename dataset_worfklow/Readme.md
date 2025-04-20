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

### Automated Steps with `run_steps_3_to_7.sh`

The `run_steps_3_to_7.sh` script automates several key steps in the data processing and model deployment pipeline.

**Purpose:**
To streamline the process from data scraping (optional, currently commented out) through model generation, testing, and uploading artefacts to Firebase Storage.

**How it works:**
1.  **Environment Setup:** Takes an environment argument (`dev` or `prod`) to determine the correct Firebase credentials (`dev-creds.json` or `prod-creds.json`) and Storage bucket.
2.  **Load Environment Variables:** Loads necessary configurations (e.g., Azure OpenAI keys) from `.env`.
3.  **Activate Virtual Environment:** Activates the Python virtual environment (`./dataset_worfklow/venv`).
4.  **Data Processing:** Includes steps (currently inactive) to:
    *   Run web scraping (`Main_scrape.py`).
    *   Fetch logos.
    *   Process scraped text and update Firestore (`add_scraped_fields_to_fire_store.py`).
5.  ** Model Creation & Testing:**
    *   Run `create_transformer_models.py` to generate sentence embeddings and a FAISS index from Firestore data, saving artefacts to `./dataset_worfklow/models/`.
    *   Run `test_model_artefacts_created.py` to validate the generated model files.
6.  **Upload Model Artefacts:**
    *   Runs `upload_model_artefacts.py` which zips the contents of `./dataset_worfklow/models` into `modelfiles.zip` and uploads it to the appropriate Firebase Storage bucket (`schemessg-v3-dev.firebasestorage.app` for dev, `schemessg.appspot.com` for prod - verify prod bucket name).

**Usage:**
Navigate to the project root directory (one level above `dataset_worfklow`) and run:
```bash
./dataset_worfklow/run_steps_3_to_7.sh <environment>
# Example for development:
./dataset_worfklow/run_steps_3_to_7.sh dev
# Example for production:
./dataset_worfklow/run_steps_3_to_7.sh prod
```
**Note:** Ensure the Python virtual environment and necessary dependencies (see `requirements.txt`) are set up first. Steps 3-6b are currently commented out in the script; uncomment them if needed.

### Credentials and Environment Files

-   **`dev-creds.json` / `prod-creds.json`**: Firebase Admin SDK service account keys for development and production environments, respectively. Obtain these from the Firebase Console (Project Settings -> Service Accounts -> Generate new private key). **Keep these files secure and do not commit them to Git.** Place them directly inside the `dataset_worfklow` directory.
-   **`.env`**: Stores environment variables, primarily Azure OpenAI API configurations (`AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, etc.). This file must be located at `dataset_worfklow/.env`.



## Utility Scripts


### `helper_scripts/` Folder
This folder contains various Node.js scripts for interacting with Firestore:
-   `export-firestore-structure.js`: Exports the Firestore database structure (collections, basic fields) from a specified environment (likely development).
-   `import-schemes-csv.js`: Imports scheme data from a CSV file into the Firestore `schemes` collection.
-   `import-firestore-structure.js`: Imports a previously exported Firestore structure into a target environment (likely production).
-   `export-firestore-structure-prod-user-logs.js`: Specifically exports user log data structures/collections from the production Firestore environment.
-   `count_documents.js`: Counts the number of documents within specified Firestore collections.

### `notebooks/` Folder
Contains Jupyter notebooks used for data processing and model development:
-   `one-time-clean-new-data.ipynb`: Appears to be a notebook for initial or specific data cleaning tasks.
-   `model-creation-transformer-laiss.ipynb`: A notebook environment for developing and experimenting with the model creation process (generating embeddings using transformers and building a FAISS index), similar to `create_transformer_models.py`.

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
