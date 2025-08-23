#!/usr/bin/env python3
"""
Python version of run_steps_3_to_7.sh that imports and uses functions directly
instead of running scripts via subprocess.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Import functions from the various scripts
from create_transformer_models import create_transformer_models
from test_model_artefacts_created import test_function
from upload_model_artefacts import upload_model_artefacts

# Import functions from Main_scrape scripts
from Main_scrape.Main_scrape import run_scraping_for_links
from Main_scrape.add_scraped_fields_to_fire_store import (
    add_scraped_fields_to_fire_store,
)
from Main_scrape.add_town_area_to_fire_store import add_town_areas


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
        creds_file = "dataset_worfklow/dev-creds.json"
        storage_bucket = dev_storage_bucket
    else:  # prod
        creds_file = "dataset_worfklow/prod-creds.json"
        storage_bucket = prod_storage_bucket

    return creds_file, storage_bucket


def check_environment_file():
    """Check if .env file exists and load it"""
    env_file = Path("dataset_worfklow/.env")
    if not env_file.exists():
        raise FileNotFoundError(
            f"Environment file '{env_file}' not found. "
            f"Please ensure your .env file is located at {env_file.absolute()}"
        )

    # Load environment variables from .env file
    load_dotenv(env_file)
    logger.info(f"Loaded environment variables from {env_file}")


def main():
    """Main function to run the workflow"""
    parser = argparse.ArgumentParser(
        description="Run steps 3-7 of the SchemesSG workflow using Python functions"
    )
    parser.add_argument(
        "environment",
        choices=["dev", "prod"],
        help="Environment to run in (dev or prod)",
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
        help="Only run specific steps (e.g., --run-only 6a 6b)",
    )

    args = parser.parse_args()

    try:
        # Setup logging
        setup_logging()

        # Validate environment
        env = validate_environment(args.environment)
        logger.info(f"Running in {env} environment")

        # Get credentials and bucket
        creds_file, storage_bucket = get_credentials_and_bucket(env)
        logger.info(f"Using credentials file: {creds_file}")
        logger.info(f"Using storage bucket: {storage_bucket}")

        # Check if we're in the right directory and load environment
        check_environment_file()

        # Define the steps to run with direct function calls
        steps = [
            (
                3,
                "Run Main_scrape.py to get scraped data in DB",
                lambda: run_scraping_for_links(creds_file),
            ),
            (
                4,
                "Get logos from website via scraping",
                lambda: logger.info("Logo scraping handled in step 3"),
            ),
            (
                5,
                "Take scraped text from DB and create new fields",
                lambda: add_scraped_fields_to_fire_store(creds_file),
            ),
            (5.5, "Add town area to fire store", lambda: add_town_areas(creds_file)),
            (
                6,
                "Recompute embeddings and faiss",
                lambda: create_transformer_models(creds_file),
            ),
            (6.5, "Test if model artefacts created are valid", lambda: test_function()),
            (
                7,
                "Upload model artefacts to firebase storage",
                lambda: upload_model_artefacts(creds_file, storage_bucket),
            ),
        ]

        # Filter steps based on arguments
        if args.run_only:
            # Convert step numbers to handle both integers and floats (6a -> 6, 6b -> 6.5)
            run_only_steps = []
            for step in args.run_only:
                if step == 6:
                    run_only_steps.extend([6, 6.5])  # Include both 6a and 6b
                else:
                    run_only_steps.append(step)
            steps = [s for s in steps if s[0] in run_only_steps]

        if args.skip_steps:
            # Convert step numbers to handle both integers and floats
            skip_steps = []
            for step in args.skip_steps:
                if step == 6:
                    skip_steps.extend([6, 6.5])  # Skip both 6a and 6b
                else:
                    skip_steps.append(step)
            steps = [s for s in steps if s[0] not in skip_steps]

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
