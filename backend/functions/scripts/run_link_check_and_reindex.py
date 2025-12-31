#!/usr/bin/env python
"""
Ad-hoc script to run link check and reindex batch job.

Usage:
    cd backend/functions
    uv run python -m scripts.run_link_check_and_reindex
"""

from dotenv import load_dotenv


load_dotenv()

import os  # noqa: E402

from fb_manager.firebaseManager import FirebaseManager  # noqa: E402
from loguru import logger  # noqa: E402


# Initialize Firebase
logger.info("Initializing Firebase...")
fm = FirebaseManager()
logger.info(f"Connected to project: {os.getenv('FB_PROJECT_ID')}")

from batch_jobs.run_link_check_and_reindex import run_link_check_and_reindex_core  # noqa: E402


def main():
    """Run link check and reindex batch job."""
    logger.info("Starting link check and reindex batch job")

    result = run_link_check_and_reindex_core()

    if result.get("success"):
        link_check = result.get("link_check", {})
        reindex = result.get("reindex", {})

        logger.info(
            f"Link check complete - Total: {link_check.get('total_checked', 0)}, "
            f"Alive: {link_check.get('alive_count', 0)}, "
            f"Dead: {link_check.get('dead_count', 0)}, "
            f"Restored: {link_check.get('restored_count', 0)}"
        )

        for dl in link_check.get("dead_links", []):
            logger.warning(f"Dead link: {dl.get('scheme_name')} - {dl.get('error')}")

        for rl in link_check.get("restored_links", []):
            logger.info(f"Restored: {rl.get('scheme_name')}")

        logger.info(
            f"Reindex complete - Processed: {reindex.get('total_processed', 0)}, "
            f"Updated: {reindex.get('embeddings_updated', 0)}"
        )
        logger.info(f"Total duration: {result.get('duration_seconds', 0)}s")
    else:
        logger.error(f"Batch job failed: {result.get('error')}")

    return result


if __name__ == "__main__":
    main()
