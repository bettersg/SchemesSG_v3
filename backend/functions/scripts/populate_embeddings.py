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
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


sys.path.insert(0, str(Path(__file__).resolve().parent))
from firestore_env import firestore_client, load_environment  # noqa: E402  (also puts backend/functions on sys.path)
from loguru import logger  # noqa: E402
from utils.reindex_embeddings import reindex_embeddings  # noqa: E402


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

    result = reindex_embeddings(firestore_client("populate_embeddings"))
    print(f"\nResult: {result}")
    return result


if __name__ == "__main__":
    sys.exit(0 if main().get("success") else 1)
