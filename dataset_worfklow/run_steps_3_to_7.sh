#!/bin/bash

set -e  # Exit immediately if any command fails

# Check if environment argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <environment>"
  echo "Please provide 'dev' or 'prod' as the environment argument."
  exit 1
fi

ENV=$1
CREDS_FILE=""
STORAGE_BUCKET="" # Variable for storage bucket

# Define bucket names (Modify PROD_STORAGE_BUCKET if needed)
DEV_STORAGE_BUCKET="schemessg-v3-dev.firebasestorage.app"
PROD_STORAGE_BUCKET="schemessg.appspot.com" # PLEASE VERIFY THIS



# Set the credentials file and storage bucket based on the environment argument
if [ "$ENV" == "dev" ]; then
  CREDS_FILE="dataset_worfklow/dev-creds.json"
  STORAGE_BUCKET=$DEV_STORAGE_BUCKET
elif [ "$ENV" == "prod" ]; then
  CREDS_FILE="dataset_worfklow/prod-creds.json"
  STORAGE_BUCKET=$PROD_STORAGE_BUCKET
else
  echo "Invalid environment specified: $ENV"
  echo "Please use 'dev' or 'prod'."
  exit 1
fi

echo "Using credentials file: $CREDS_FILE"
echo "Using storage bucket: $STORAGE_BUCKET"

cd .. # Change to project root directory first

# Check for .env file
ENV_FILE="dataset_worfklow/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found in the $(pwd)/dataset_worfklow directory."
    echo "Please ensure your .env file is located at dataset_worfklow/.env."
    exit 1
fi

# Load environment variables from .env file and export them
set -a
source "$ENV_FILE"
set +a
echo "Loaded environment variables from $ENV_FILE"

# Activate the virtual environment located in dataset_worfklow
source dataset_worfklow/venv/bin/activate

# echo "starting step 3"
# # # step 3: run Main_scrape.py to get scraped data in DB
# python -m dataset_worfklow.Main_scrape.Main_scrape "$CREDS_FILE"

# # step 4 get logos from website via scraping

# echo "starting step 5"
# # step 5: Take scraped text from DB, and create new fields
# python -m dataset_worfklow.Main_scrape.add_scraped_fields_to_fire_store "$CREDS_FILE"

echo "starting step 5b"
python -m dataset_worfklow.Main_scrape.add_town_area_and_summary_to_fire_store "$CREDS_FILE" --onemap_token "$ONEMAP_TOKEN"

# echo "starting step 6a"
# # step 6a: Run to recompute embeddings and faiss
# python -m dataset_worfklow.create_transformer_models "$CREDS_FILE"

# echo "starting step 6b"
# # step 6b: Test if model artefacts created are valid
# python -m dataset_worfklow.test_model_artefacts_created "$CREDS_FILE"

# echo "only run step 7 if you are satisfied with results from steps 6b"
# # step 7: Upload model artefacts to firebase storage
# python -m dataset_worfklow.upload_model_artefacts "$CREDS_FILE" "$STORAGE_BUCKET"
