# Schemes Reimagined

The inspiration behind **Schemesv3** arose from a common but profound concern: the difficulty of navigating social support systems. Our project was fueled by the desire to create a bridge between Singaporeans and the aid they need, especially during life's most trying times.

The technical journey to realize this vision has been nothing short of transformative. We began with an existing database of schemes, enriching it through meticulous manual curation and leveraging **web scraping** techniques to expand our dataset. This ensured that we have a robust and comprehensive list of schemes complete with relevant metadata.

For data processing, we employed **NLP (Natural Language Processing)** techniques, using tools like **spacy** and **re** for preprocessing and lemmatization. The **sentence-transformers all-mpnet-base-v2** model then helped us generate embeddings that truly captured the nuances of each scheme's purpose. We used **FAISS** to create a powerful indexing system, enabling users to search and retrieve scheme information efficiently.



### What's here:

* [Flask](https://docs.streamlit.io/) on the frontend
* [FastAPI](https://fastapi.tiangolo.com/) on the backend
* Backend and frontend can be deployed with Docker

> From inside the `backend` folder:
Download the model files from Google Drive or build yourself using model-creation-transformer-laiss.ipynb
Run export KMP_DUPLICATE_LIB_OK=TRUE if you facing issue
You can serve the API with `uvicorn fast_api.api:app --reload` (default port is `8000`)

> From inside the `root` folder:
<!-- Create .env file and make sure you have BigQuery setup  -->
You can serve the frontend with `python app.py`

### Docker
Refer to Readme files in backend folder
