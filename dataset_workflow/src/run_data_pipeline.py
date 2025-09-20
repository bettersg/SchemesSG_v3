#!/usr/bin/env python3
"""
Python version of run_steps_3_to_7.sh that imports and uses functions directly
instead of running scripts via subprocess.
"""

import os
import sys
import argparse
from pathlib import Path
from loguru import logger

# Add the current directory to Python path so we can import src modules
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import functions from the various scripts
from src.create_transformer_models import create_transformer_models
from src.upload_model_artefacts import upload_model_artefacts
from src.test_model_artefacts_created import test_function
# Import functions from Main_scrape scripts
from src.Main_scrape.Main_scrape import run_scraping_for_links
from src.Main_scrape.add_scraped_fields_to_fire_store import (
    add_scraped_fields_to_fire_store,
)
from src.Main_scrape.add_town_area_to_fire_store import add_town_areas


def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        colorize=True,
        backtrace=True,
    )


def validate_environment(env):
    """Validate the environment argument"""
    if env not in ["dev", "prod"]:
        raise ValueError(
            f"Invalid environment specified: {env}. Please use 'dev' or 'prod'."
        )
    return env


def get_credentials_and_bucket(env):
    """Get credentials file path and storage bucket based on environment"""
    # Define bucket names
    dev_storage_bucket = "schemessg-v3-dev.firebasestorage.app"
    prod_storage_bucket = "schemessg.appspot.com"  # PLEASE VERIFY THIS


    if env == "dev":
        storage_bucket = dev_storage_bucket
        creds_file = str(Path(__file__).parent.parent / "dev-creds.json")
    elif env == "prod":  # prod
        storage_bucket = prod_storage_bucket
        creds_file = str(Path(__file__).parent.parent / "prod-creds.json")
    else:
        raise ValueError(f"Invalid environment specified: {env}. Please use 'dev' or 'prod'.")

    return creds_file, storage_bucket

def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(
        description="Run steps 1-7 of the SchemesSG workflow using Python functions"
    )
    parser.add_argument(
        "environment",
        choices=["dev", "prod"],
        help="Environment to run in (dev or prod) - REQUIRED",
    )
    parser.add_argument(
        "--doc_ids",
        nargs="+",
        type=str,
        help="Doc ids to process (e.g., --doc_ids 00uFr8EP5kJsqgh7G33h 00uFr8EP5kJsqgh7G33h)",
    )
    parser.add_argument(
        "--skip-steps",
        nargs="+",
        type=int,
        help="Steps to skip (e.g., --skip-steps 3 4 5)",
    )
    parser.add_argument(
        "--run-only",
        nargs="+",
        type=int,
        help="Only run specific steps (e.g., --run-only 6)",
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        # This happens when argparse encounters an error (like missing required args)
        print("\n" + "="*60)
        print("USAGE EXAMPLES:")
        print("="*60)
        print("python run_data_pipeline.py dev")
        print("python run_data_pipeline.py prod")
        print("python run_data_pipeline.py dev --run-only 1 2 3")
        print("python run_data_pipeline.py prod --skip-steps 4 5")
        print("python run_data_pipeline.py dev --doc_ids 00uFr8EP5kJsqgh7G33h")
        print("="*60)
        sys.exit(1)

    try:
        # Setup logging
        setup_logging()

        # Validate environment
        env = validate_environment(args.environment)
        logger.info(f"Running in {env} environment")

        doc_ids = args.doc_ids
        if doc_ids:
            logger.info(f"Processing doc ids: {doc_ids}")
            doc_ids = [doc_id.strip() for doc_id in doc_ids]
        else:
            logger.info("Processing all doc ids")

        # Get credentials and bucket
        creds_file, storage_bucket = get_credentials_and_bucket(env)
        logger.info(f"Using credentials file: {creds_file}")
        logger.info(f"Using storage bucket: {storage_bucket}")

        # Initialize Firebase once
        logger.info("Initializing Firebase...")
        import firebase_admin
        from firebase_admin import credentials, firestore

        cred = credentials.Certificate(creds_file)
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase initialized successfully")

        # Define the steps to run with direct function calls
        steps = [
            (
                1,
                "Run Main_scrape.py to get scraped data in DB",
                lambda: run_scraping_for_links(db, process_specific_doc_ids=doc_ids),
            ),
            (
                2,
                "Get logos from website via scraping",
                lambda: logger.info("Logo scraping handled in step 2"),
            ),
            (
                3,
                "Take scraped text from DB and create new fields",
                lambda: add_scraped_fields_to_fire_store(db, doc_ids),
            ),
            (
                4,
                "Add town area to fire store",
                lambda: add_town_areas(db, doc_ids),
            ),
            (
                5,
                "Recompute embeddings and faiss",
                lambda: create_transformer_models(db),
            ),
            (
                6,
                "Test if model artefacts created are valid",
                lambda: test_function(db),
            ),
            (
                7,
                "Upload model artefacts to firebase storage",
                lambda: upload_model_artefacts(creds_file, storage_bucket),
            ),
        ]

        # Filter steps based on arguments
        if args.run_only:
            steps = [s for s in steps if s[0] in args.run_only]

        if args.skip_steps:
            steps = [s for s in steps if s[0] not in args.skip_steps]

        # Run the selected steps
        logger.info(f"Running {len(steps)} steps")
        for step_num, description, step_func in steps:
            logger.info(f"Step {step_num}: {description}")
            try:
                step_func()
                logger.success(f"Step {step_num} completed successfully")
            except Exception as e:
                logger.error(f"Step {step_num} failed: {e}")
                raise

        logger.success("All selected steps completed successfully!")

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
