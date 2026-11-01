"""
Populate schemes_embeddings collection for Firestore vector search.

Runs the same reindex as the weekly scheduled job (utils.reindex_embeddings):
same embedding text, renamed-term synonyms, inactive/retired schemes skipped
and stale embeddings deleted. Original 'schemes' collection is unchanged.

Usage:
    cd backend/functions
    uv run python scripts/populate_embeddings.py --dev   # Uses .env.dev (schemessg-v3-dev)
    uv run python scripts/populate_embeddings.py --prod  # Uses .env.prod (schemessg), asks to confirm
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


# Allow `python scripts/populate_embeddings.py` as well as `python -m scripts.populate_embeddings`.
FUNCTIONS_DIR = Path(__file__).resolve().parents[1]
if str(FUNCTIONS_DIR) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_DIR))

from dotenv import load_dotenv  # noqa: E402
from firebase_admin import credentials, firestore, initialize_app  # noqa: E402
from loguru import logger  # noqa: E402
from utils.reindex_embeddings import reindex_embeddings  # noqa: E402


ENVIRONMENTS = {"dev": (".env.dev", "schemessg-v3-dev"), "prod": (".env.prod", "schemessg")}


def parse_args(argv: Optional[Sequence[str]] = None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Populate schemes_embeddings collection for Firestore vector search.")
    env_group = parser.add_mutually_exclusive_group(required=True)
    env_group.add_argument(
        "--dev",
        action="store_true",
        help="Run against dev project (schemessg-v3-dev) using .env.dev",
    )
    env_group.add_argument(
        "--prod",
        action="store_true",
        help="Run against production project (schemessg) using .env.prod",
    )
    return parser.parse_args(argv)


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


def firestore_client():
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
    app = initialize_app(cred, name="populate_embeddings")
    return firestore.client(app)


def main(argv: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    args = parse_args(argv)
    env = "prod" if args.prod else "dev"
    project_id = load_environment(env)

    if env == "prod":
        logger.warning(f"You are about to populate embeddings in PRODUCTION ({project_id})")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(0)

    result = reindex_embeddings(firestore_client())
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    sys.exit(0 if main().get("success") else 1)
