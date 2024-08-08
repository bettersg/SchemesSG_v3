# Schemes Reimagined

The inspiration behind **Schemesv3** arose from a common but profound concern: the difficulty of navigating social support systems. Our project was fueled by the desire to create a bridge between Singaporeans and the aid they need, especially during life's most trying times.

The technical journey to realize this vision has been nothing short of transformative. We began with an existing database of schemes, enriching it through meticulous manual curation and leveraging **web scraping** techniques to expand our dataset. This ensured that we have a robust and comprehensive list of schemes complete with relevant metadata.

For data processing, we employed **NLP (Natural Language Processing)** techniques, using tools like **spacy** and **re** for preprocessing and lemmatization. The **sentence-transformers all-mpnet-base-v2** model then helped us generate embeddings that truly captured the nuances of each scheme's purpose. We used **FAISS** to create a powerful indexing system, enabling users to search and retrieve scheme information efficiently.


## Getting started
### Prerequisites

Ensure you have the following installed on your machine:

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Docker Compose is included with Docker Desktop
- **Download model files**: Download the model files from Google Drive or build yourself using model-creation-transformer-laiss.ipynb 

### Developing in local environment
```bash
# Install dependencies
pip install -r frontend/requirements.txt

# Launch frontend
cd frontend
python app.py

# In a new terminal, deploy backend locally
cd ../backend
uvicorn fast_api.api:app --host 0.0.0.0 --port 8000

# Access the frontend service:
# Open your browser and navigate to http://localhost:9099.
```

### Developing in local docker
```bash
# Build the image and run the containers
docker compose up --build

# Access the frontend service:
# Open your browser and navigate to http://localhost:9099.
```

# Notes
- Ensure your Docker Desktop is running before executing any Docker commands.
- If you encounter any issues, check the Docker logs for more information.
