"""
Monthly Scheme Content Change Check Batch Job.

Scheduled function (runs monthly at 10am on the 1st of every month) that:
1. Fetches all schemes from the "schemes" Firestore collection.
2. Delegates checking to the scheme-processor service (Cloud Run / Docker on port 8081)
   where Playwright, crawl4ai, Pydoll, and Chromium are configured.
3. Detects content changes, creates baseline fingerprints, or flags out-of-date fields in contentChecks.

Can also be run locally via:
    uv run python -c "from batch_jobs.run_content_check import run_content_check_core; run_content_check_core()"
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

import google.auth.compute_engine
import google.auth.transport.requests
import requests
from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from google.oauth2 import service_account
from loguru import logger


# URL for scheme-processor service
# In local dev: http://scheme-processor:8081 (docker network)
# In production: Cloud Run URL
PROCESSOR_SERVICE_URL = os.getenv("PROCESSOR_SERVICE_URL", "http://localhost:8081")

# Ensure scheme-processor is on sys.path so app.content_check can be imported for local/direct calls
_scheme_processor_dir = str(Path(__file__).resolve().parents[2] / "scheme-processor")
if _scheme_processor_dir not in sys.path:
    sys.path.insert(0, _scheme_processor_dir)

from app.content_check import ContentStore, check_scheme
from app.services.scraper import scrape_url


def get_identity_token(audience: str) -> str:
    """Get identity token for Cloud Run authentication."""
    try:
        # Try to get credentials from GOOGLE_APPLICATION_CREDENTIALS (service account)
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            credentials = service_account.IDTokenCredentials.from_service_account_file(
                creds_path, target_audience=audience
            )
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            return credentials.token

        # Fallback to compute engine credentials (works on GCP - Cloud Functions/Run)
        auth_req = google.auth.transport.requests.Request()
        credentials = google.auth.compute_engine.IDTokenCredentials(
            request=auth_req,
            target_audience=audience,
            use_metadata_identity_endpoint=True,
        )
        credentials.refresh(auth_req)
        return credentials.token
    except Exception as e:
        logger.warning(f"Could not get identity token: {e}")
        return ""


def check_single_scheme_via_processor(
    doc_id: str,
    processor_url: str = PROCESSOR_SERVICE_URL,
    timeout: int = 300,
) -> Dict[str, Any]:
    """
    Call scheme-processor service /content-check endpoint for a single scheme.

    Delegates web crawling (Playwright/crawl4ai/Pydoll) and AI review to the
    container with full browser capabilities and Cloudflare bypass support.
    """
    headers = {"Content-Type": "application/json"}
    if processor_url.startswith("https://"):
        try:
            token = get_identity_token(processor_url)
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info(f"Got identity token for Cloud Run auth (token length: {len(token)})")
        except Exception as auth_error:
            logger.error(f"Failed to get identity token: {auth_error}")

    url = f"{processor_url.rstrip('/')}/content-check"
    try:
        response = requests.post(
            url,
            json={"scheme_ids": [doc_id]},
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            raise ValueError(f"Empty results from scheme-processor for {doc_id}")
        return results[0]

    except requests.exceptions.Timeout:
        logger.error(f"Scheme-processor timeout for {doc_id}")
        return {
            "scheme_id": doc_id,
            "outcome": "error",
            "detail": "Processing timeout - service did not respond in time",
            "check_id": None,
        }

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Scheme-processor connection error for {doc_id}: {e}")
        return {
            "scheme_id": doc_id,
            "outcome": "error",
            "detail": f"Could not connect to processor service: {e}",
            "check_id": None,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Scheme-processor error for {doc_id}: {e}")
        return {
            "scheme_id": doc_id,
            "outcome": "error",
            "detail": str(e),
            "check_id": None,
        }


def check_single_scheme(
    doc_id: str,
    store: Optional[ContentStore] = None,
    scrape_fn: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
    review_fn: Optional[Callable[[Dict[str, Any], str], Awaitable[List[Dict[str, Any]]]]] = None,
    now: Optional[datetime] = None,
    processor_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check content for a single scheme document.

    If processor_url is provided (or PROCESSOR_SERVICE_URL is set and no custom
    scrape/review functions are passed), delegates execution to the scheme-processor
    service. Otherwise, runs check_scheme locally.

    Args:
        doc_id: Firestore document ID for the scheme
        store: ContentStore instance backed by Firestore
        scrape_fn: Optional async scraper function
        review_fn: Optional async review function
        now: Optional datetime for timestamping
        processor_url: Optional base URL for scheme-processor service

    Returns:
        Dict with keys: scheme_id, outcome, detail, check_id
    """
    target_processor_url = processor_url if processor_url is not None else PROCESSOR_SERVICE_URL

    # Delegate to scheme-processor if URL is configured and no in-memory mocks are passed
    if target_processor_url and scrape_fn is None and review_fn is None:
        return check_single_scheme_via_processor(doc_id, processor_url=target_processor_url)

    # Local fallback / test execution
    if store is None:
        store = ContentStore(get_firestore_client())

    scrape = scrape_url
    if scrape is None:
        raise ValueError("No scraper function available for content check")

    kwargs: Dict[str, Any] = {}
    if review_fn is not None:
        kwargs["review"] = review_fn
    if now is not None:
        kwargs["now"] = now

    return asyncio.run(check_scheme(doc_id, store, scrape, **kwargs))


def run_content_check_core(
    db=None,
    store: Optional[ContentStore] = None,
    scrape_fn: Optional[Callable[[str], Awaitable[Dict[str, Any]]]] = None,
    review_fn: Optional[Callable[[Dict[str, Any], str], Awaitable[List[Dict[str, Any]]]]] = None,
    scheme_ids: Optional[List[str]] = None,
    now: Optional[datetime] = None,
    processor_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core logic for monthly content checking across all schemes in Firestore.

    Can be called directly for local testing or invoked by the scheduled function.

    Args:
        db: Firestore client (optional, will create via get_firestore_client if not provided)
        store: ContentStore instance (optional, created from db if not provided)
        scrape_fn: Optional async scraper function
        review_fn: Optional async review function
        scheme_ids: Optional list of scheme document IDs to check (defaults to all schemes)
        now: Optional datetime for timestamping
        processor_url: Optional scheme-processor service URL

    Returns:
        Dict with execution summary and stats
    """
    start_time = time.time()
    logger.info("Starting monthly content check batch job...")

    try:
        if db is None:
            db = get_firestore_client()
        if store is None:
            store = ContentStore(db)

        # Step 1: Fetch schemes to check
        if scheme_ids is None:
            logger.info("Fetching schemes from Firestore 'schemes' collection...")
            schemes_ref = db.collection("schemes")
            docs = schemes_ref.stream()
            scheme_ids = [doc.id for doc in docs]

        total_count = len(scheme_ids)
        logger.info(f"Found {total_count} schemes to process for content check")

        outcomes: Dict[str, int] = {
            "baseline": 0,
            "unchanged": 0,
            "flagged": 0,
            "skipped": 0,
            "scrape_failed": 0,
            "not_found": 0,
            "error": 0,
        }
        flagged_schemes: List[Dict[str, Any]] = []
        failed_schemes: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []

        if total_count == 0:
            end_time = time.time()
            return {
                "success": True,
                "total_checked": 0,
                "outcomes": outcomes,
                "flagged_schemes": [],
                "failed_schemes": [],
                "results": [],
                "duration_seconds": round(end_time - start_time, 2),
            }

        # Step 2: Check schemes concurrently
        max_workers = max(1, min(20, total_count))  # Cap at 20 concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    check_single_scheme,
                    doc_id,
                    store,
                    scrape_fn,
                    review_fn,
                    now,
                    processor_url,
                ): doc_id
                for doc_id in scheme_ids
            }

            for future in as_completed(futures):
                doc_id = futures[future]
                try:
                    res = future.result()
                    results.append(res)
                    outcome = res.get("outcome", "error")
                    if outcome in outcomes:
                        outcomes[outcome] += 1
                    else:
                        outcomes["error"] += 1

                    if outcome == "flagged":
                        flagged_schemes.append(
                            {
                                "doc_id": doc_id,
                                "check_id": res.get("check_id"),
                                "detail": res.get("detail"),
                            }
                        )
                    elif outcome in ("scrape_failed", "error"):
                        failed_schemes.append(
                            {
                                "doc_id": doc_id,
                                "outcome": outcome,
                                "detail": res.get("detail"),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error checking scheme {doc_id}: {e}")
                    outcomes["error"] += 1
                    failed_schemes.append(
                        {
                            "doc_id": doc_id,
                            "outcome": "error",
                            "detail": str(e),
                        }
                    )

        end_time = time.time()
        duration_seconds = round(end_time - start_time, 2)

        logger.info(f"Content check complete in {duration_seconds}s. Total: {total_count}. Outcomes: {outcomes}")

        return {
            "success": True,
            "total_checked": total_count,
            "outcomes": outcomes,
            "flagged_schemes": flagged_schemes,
            "failed_schemes": failed_schemes,
            "results": results,
            "duration_seconds": duration_seconds,
        }

    except Exception as e:
        logger.error(f"Content check batch job failed: {e}")
        return {"success": False, "error": str(e)}


@scheduler_fn.on_schedule(
    schedule="0 10 1 * *",  # Run at 10am on 1st of every month
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
    timeout_sec=540,  # 9 minutes max
    retry_count=1,
)
def scheduled_content_check(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Monthly scheduled function for checking scheme content changes.

    Runs on the 1st of every month at 10am SGT (after weekly link check runs at 9am).
    Checks all schemes in the schemes collection for content changes.

    Args:
        event: Scheduled event object from Firebase
    """
    logger.info(f"Scheduled content check triggered at {event.schedule_time}")
    result = run_content_check_core()
    logger.info(f"Scheduled content check result: {json.dumps(result, default=str)}")
