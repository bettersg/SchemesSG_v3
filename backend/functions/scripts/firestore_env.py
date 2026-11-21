"""Env file loading and Firestore client for the operator scripts in this folder.

`load_environment("dev"|"prod")` loads `.env.dev` / `.env.prod` from backend/functions and exits unless the file
names the expected project, so a mislabelled env file can never point a dev command at prod.
"""

import os
import sys
from pathlib import Path


# Allow `python scripts/<name>.py` as well as `python -m scripts.<name>`.
FUNCTIONS_DIR = Path(__file__).resolve().parents[1]
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))

from dotenv import load_dotenv  # noqa: E402
from firebase_admin import credentials, firestore, initialize_app  # noqa: E402
from loguru import logger  # noqa: E402


ENVIRONMENTS = {"dev": (".env.dev", "schemessg-v3-dev"), "prod": (".env.prod", "schemessg")}


def load_environment(env: str) -> str:
    """Load the env file for `env` and return its project id; exit if the file is missing or names another project."""
    env_name, expected_project = ENVIRONMENTS[env]
    env_file = FUNCTIONS_DIR / env_name
    if not env_file.exists():
        logger.error(f"Env file not found: {env_file}")
        sys.exit(1)
    load_dotenv(env_file, override=True)
    project_id = os.getenv("FB_PROJECT_ID")
    if project_id != expected_project:
        logger.error(f"{env_name} points at {project_id}, expected {expected_project}")
        sys.exit(1)
    logger.info(f"Loaded {env_name} ({project_id})")
    return expected_project


def firestore_client(app_name: str):
    """Firestore client from the FB_* service account variables of the loaded env file."""
    cred = credentials.Certificate(
        {
            "type": os.getenv("FB_TYPE"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI"),
            "token_uri": os.getenv("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        }
    )
    return firestore.client(initialize_app(cred, name=app_name))
