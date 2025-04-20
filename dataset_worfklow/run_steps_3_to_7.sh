#!/bin/bash

set -e  # Exit immediately if any command fails

cd ../backend # switch to this directory to activate virtual env
source functions/venv/bin/activate

cd .. # change to root directory for running rest of scripts

# echo "starting step 3"
# # step 3: run Main_scrape.py to get scraped data in DB
# python -m dataset_worfklow.Main_scrape.Main_scrape

# step 4 get logos from website via scraping

#echo "starting step 5"
# step 5: Take scraped text from DB, and create new fields
#python -m dataset_worfklow.Main_scrape.add_scraped_fields_to_fire_store

echo "starting step 6a"
# step 6a: Run to recompute embeddings and faiss
python -m dataset_worfklow.create_transformer_models

echo "starting step 6b"
# step 6b: Test if model artefacts created are valid
python -m dataset_worfklow.test_model_artefacts_created

echo "only run step 7 if you are satisfied with results from steps 6b"
# step 7: Upload model artefacts to firebase storage
python -m dataset_worfklow.upload_model_artefacts