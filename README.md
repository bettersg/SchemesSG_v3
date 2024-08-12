# Schemes Reimagined

The inspiration behind **Schemesv3** arose from a common but profound concern: the difficulty of navigating social support systems. Our project was fueled by the desire to create a bridge between Singaporeans and the aid they need, especially during life's most trying times.

The technical journey to realize this vision has been nothing short of transformative. We began with an existing database of schemes, enriching it through meticulous manual curation and leveraging **web scraping** techniques to expand our dataset. This ensured that we have a robust and comprehensive list of schemes complete with relevant metadata.

For data processing, we employed **NLP (Natural Language Processing)** techniques, using tools like **spacy** and **re** for preprocessing and lemmatization. The **sentence-transformers all-mpnet-base-v2** model then helped us generate embeddings that truly captured the nuances of each scheme's purpose. We used **FAISS** to create a powerful indexing system, enabling users to search and retrieve scheme information efficiently.


## Getting started
### Prerequisites

Ensure you have the following installed on your machine:

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: Docker Compose is included with Docker Desktop
- **Poetry 1.8.3**: [Install Poetry](https://python-poetry.org/docs/#installation)
- **Python 3.9 above**: [Install Python](https://www.python.org/downloads/)
- **Download model files**: Download the model files from Google Drive or build yourself using model-creation-transformer-faiss.ipynb 

### Developing in local environment

We use Poetry as the dependency manager because it provides a consistent and straightforward way to manage dependencies and virtual environments across both Windows and Mac systems.

#### Poetry config set up (Must Run)
```bash
# ensure all poetry environments are installed in the directory
poetry config virtualenvs.in-project true
```

#### Developing in jupyter notebooks

You may launch jupyter notebook via poetry or use visual studio code's native jupyter extension.

1. Launch jupyter notebook via poetry
  ```bash
  # Change directory to backend or frontend because the pyproject.toml file is in those directories
  cd backend

  # deactivate any existing virtual environment, i.e. anaconda
  deactivate

  # Create new python virtual env and install dependencies using poetry
  poetry install 
  # notice that a .venv/ directory will be installed in the directory

  # Initialize python virtual env
  poetry shell

  # launch jupyter notebook
  jupyter notebook
  ```

2. Launch visual studio code and open jupyter notebook (preferred method)

#### Deploy frontend and backend locally 

```bash
# Install dependencies for frontend and deploy flask app w/ vanilla js
cd frontend
deactivate
poetry install
poetry run python app.py

# In a new terminal, install dependencies for backend and deploy locally
cd ../backend
deactivate
poetry install
poetry run uvicorn fast_api.api:app --host 0.0.0.0 --port 8000

# If the virtual environment fails to build due to an invalid poetry.lock file:
## Regenerate poetry.lock file and re-install
poetry lock --no-update
poetry install

# Access the frontend service:
# Open your browser and navigate to http://localhost:9099.
```

### Deployment in local docker

Local Docker environment is designed to closely replicate our production environments. This ensures that the application behaves consistently from development to deployment, minimizing issues that might arise due to differences in individual developer setups.

For example, if you make changes to core logic in `backend/` directory, you have to deploy the both frontend and backend via docker and perform functionality tests manually.

```bash
# Build the image and run the containers
docker compose up --build

# Access the frontend service:
# Open your browser and navigate to http://localhost:9099.
```

### Adding Development Dependencies

To add dependencies specifically for development (e.g., testing frameworks, linters, etc.), you can use Poetry's `add` command with the `--group dev` option. This ensures that these dependencies are only installed in development environments and not in production.

<details>
  <summary>Poetry useful commands</summary>

    ```bash
    # Activate the Poetry environment
    poetry shell

    # Install all dependencies (including development dependencies if needed)
    poetry install

    # Add a production dependency
    poetry add <dependency_name>
    # e.g. poetry add pandas
    # e.g. poetry add pandas@^2.2.2

    # Add a development dependency
    poetry add --group dev <dependency_name>

    # Remove a dependency
    poetry remove <dependency_name>

    # Regenerate the poetry.lock file without updating dependencies
    poetry lock --no-update

    # List all installed dependencies
    poetry show --all

    # List only production dependencies
    poetry show --only main

    # List only development dependencies
    poetry show --only dev

    # Check the status of dependencies (e.g., if they are outdated)
    poetry show --outdated

    # Run a script or command within the Poetry environment
    poetry run <command>
    # e.g. poetry run python app.py 

    # Check the project's environment and configuration
    poetry check
    ```
</details>

---

# Notes
- Ensure your Docker Desktop is running before executing any Docker commands.
- If you encounter any issues, you can pm Traci on slack or whatsapp.
