"""
Issue, list, or revoke a partner API key for the partner API (`partner_api`).

Only the SHA-256 hash of a key is ever stored, as the `partner_keys` document ID.
The plaintext key is printed once, here, and cannot be recovered afterwards — if
it is lost, revoke it and issue a new one.

Usage:
    cd backend/functions

    # Sandbox first, always (see docs/partner-api-runbook.md)
    uv run python scripts/issue_partner_key.py --dev  issue --consumer carecompass --rate-limit 60

    # Production, only after the partner has verified against sandbox
    uv run python scripts/issue_partner_key.py --prod issue --consumer carecompass --rate-limit 60

    uv run python scripts/issue_partner_key.py --dev list
    uv run python scripts/issue_partner_key.py --dev revoke --consumer carecompass
"""

import argparse
import os
import secrets
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
from loguru import logger
from utils.partner_auth import PARTNER_KEYS_COLLECTION, hash_key


KEY_PREFIX = "sk_schemes_"
KEY_BYTES = 32


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Manage partner API keys for partner_api.")
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

    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue", help="Issue a new key for a consumer")
    issue.add_argument("--consumer", required=True, help="Partner identifier, e.g. carecompass")
    issue.add_argument("--rate-limit", type=int, default=60, help="Requests per minute (default: 60)")

    sub.add_parser("list", help="List issued keys (hashes only)")

    revoke = sub.add_parser("revoke", help="Revoke every key for a consumer")
    revoke.add_argument("--consumer", required=True, help="Partner identifier to revoke")

    return parser.parse_args()


def load_environment(is_prod: bool) -> None:
    """Load the appropriate environment file."""
    name = ".env.prod" if is_prod else ".env.dev"
    env_file = os.path.join(os.path.dirname(__file__), "..", name)
    if not os.path.exists(env_file):
        logger.error(f"Env file not found: {env_file}")
        sys.exit(1)
    load_dotenv(env_file, override=True)
    logger.info(f"Loaded environment ({name})")


def get_firestore_client():
    """Initialise the Firebase Admin SDK from the loaded environment."""
    private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": os.getenv("FB_TYPE"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI"),
            "token_uri": os.getenv("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        }
    )
    try:
        initialize_app(cred)
    except ValueError:
        pass  # Already initialized
    return firestore.client()


def issue_key(db, consumer: str, rate_limit: int) -> None:
    """Generate a key, store only its hash, and print the plaintext once."""
    raw_key = f"{KEY_PREFIX}{secrets.token_urlsafe(KEY_BYTES)}"
    db.collection(PARTNER_KEYS_COLLECTION).document(hash_key(raw_key)).set(
        {
            "consumer": consumer,
            "active": True,
            "created_at": datetime.now(tz=timezone.utc),
            "rate_limit_per_min": rate_limit,
        }
    )
    project = os.getenv("FB_PROJECT_ID")
    print()
    print(f"  Issued key for consumer '{consumer}' on project '{project}'")
    print(f"  Rate limit: {rate_limit} requests/minute")
    print()
    print(f"  {raw_key}")
    print()
    print("  Shown once and not stored. Hand it over out-of-band, never in")
    print("  plaintext email or Slack. If lost, revoke and issue a new one.")
    print()


def list_keys(db) -> None:
    """Print issued keys, by hash — plaintext keys are not recoverable."""
    docs = list(db.collection(PARTNER_KEYS_COLLECTION).stream())
    if not docs:
        print("No partner keys issued on this project.")
        return

    print(f"{'consumer':<24} {'active':<8} {'rpm':<6} {'created':<22} hash")
    for doc in docs:
        data = doc.to_dict() or {}
        created = data.get("created_at")
        created_str = created.isoformat() if hasattr(created, "isoformat") else str(created or "-")
        print(
            f"{str(data.get('consumer', '-')):<24} "
            f"{str(data.get('active', False)):<8} "
            f"{str(data.get('rate_limit_per_min', '-')):<6} "
            f"{created_str:<22} "
            f"{doc.id[:16]}..."
        )


def revoke_consumer(db, consumer: str) -> None:
    """Deactivate every key belonging to a consumer. Takes effect next request."""
    docs = list(
        db.collection(PARTNER_KEYS_COLLECTION).where("consumer", "==", consumer).stream()
    )
    if not docs:
        print(f"No keys found for consumer '{consumer}'.")
        return

    for doc in docs:
        doc.reference.update({"active": False, "revoked_at": datetime.now(tz=timezone.utc)})
    print(f"Revoked {len(docs)} key(s) for '{consumer}'. Effective on their next request.")


def main() -> None:
    args = parse_args()
    load_environment(args.prod)

    if args.prod:
        project = os.getenv("FB_PROJECT_ID")
        confirm = input(f"About to modify PRODUCTION project '{project}'. Type the project id to continue: ")
        if confirm.strip() != project:
            print("Aborted.")
            sys.exit(1)

    db = get_firestore_client()

    if args.command == "issue":
        issue_key(db, args.consumer, args.rate_limit)
    elif args.command == "list":
        list_keys(db)
    elif args.command == "revoke":
        revoke_consumer(db, args.consumer)


if __name__ == "__main__":
    main()
