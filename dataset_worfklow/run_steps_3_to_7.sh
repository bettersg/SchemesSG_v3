cd ../backend

source functions/venv/bin/activate

# step 3: Manual > run Main_scrape.py to get scraped data in DB
python -m dataset_worfklow.Main_scrape.Main_scrape

# step 5: Take scraped text from DB, and create new fields
python -m dataset_worfklow.Main_scrape.add_scraped_fields_to_fire_store

# step 6: Run model-creation-transformer-laiss.ipynb to recompute embeddings and faiss
python -m dataset_worfklow.create_transformer_models

# step 7: Upload model artefacts to firebase storage
python -m dataset_worfklow.upload_model_artefacts