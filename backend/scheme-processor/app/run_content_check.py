"""
Monthly Scheme Content Change Check Batch Job (Cloud Run Job).

Executes inside the scheme-processor container on Cloud Run (triggered monthly on schedule "0 10 1 * *").
Checks all schemes in Firestore for content changes and flags out-of-date fields in contentChecks.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from app.clients.firestore import get_firestore_client
from app.content_check import ContentStore, check_scheme
from app.services.scraper import scrape_url


async def scrape_for_content_check(url: str) -> Dict[str, Any]:
    return await scrape_url(url, content_check=True)


def check_single_scheme_in_job(
    doc_id: str,
    store: ContentStore,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Check a single scheme directly in-process using Playwright/crawl4ai."""
    return asyncio.run(
        check_scheme(
            scheme_id=doc_id,
            store=store,
            scrape=scrape_for_content_check,
            now=now,
        )
    )


def run_job_core(
    db=None,
    store: Optional[ContentStore] = None,
    scheme_ids: Optional[List[str]] = None,
    concurrency: int = 2,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Run content check across schemes directly within Cloud Run.

    Args:
        db: Firestore client
        store: ContentStore instance
        scheme_ids: Optional list of scheme document IDs (defaults to all schemes)
        concurrency: Max concurrent browser scrapers (defaults to 2 for memory safety)
        now: Optional timestamp

    Returns:
        Dict with execution summary
    """
    start_time = time.time()
    now = now or datetime.now(timezone.utc)
    logger.info("Starting Cloud Run monthly content check job...")

    try:
        if db is None:
            db = get_firestore_client()
        if store is None:
            store = ContentStore(db)

        if scheme_ids is None:
            logger.info("Streaming scheme IDs from Firestore 'schemes' collection...")
            scheme_ids = [doc.id for doc in db.collection("schemes").stream()]

        total_count = len(scheme_ids)
        logger.info(f"Total schemes to check: {total_count} (concurrency: {concurrency})")

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
            duration_seconds = round(time.time() - start_time, 2)
            return {
                "success": True,
                "total_checked": 0,
                "outcomes": outcomes,
                "flagged_schemes": [],
                "failed_schemes": [],
                "duration_seconds": duration_seconds,
            }

        max_workers = max(1, min(concurrency, total_count))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(check_single_scheme_in_job, doc_id, store, now): doc_id
                for doc_id in scheme_ids
            }
            for future in as_completed(futures):
                doc_id = futures[future]
                try:
                    res = future.result()
                    results.append(res)
                    outcome = res.get("outcome", "error")
                    outcomes[outcome] = outcomes.get(outcome, 0) + 1
                    if outcome == "flagged":
                        flagged_schemes.append(
                            {"doc_id": doc_id, "check_id": res.get("check_id"), "detail": res.get("detail")}
                        )
                    elif outcome in ("scrape_failed", "error"):
                        failed_schemes.append(
                            {"doc_id": doc_id, "outcome": outcome, "detail": res.get("detail")}
                        )
                except Exception as e:
                    logger.error(f"Error checking scheme {doc_id}: {e}")
                    outcomes["error"] = outcomes.get("error", 0) + 1
                    failed_schemes.append({"doc_id": doc_id, "outcome": "error", "detail": str(e)})

        duration_seconds = round(time.time() - start_time, 2)
        logger.info(f"Content check complete in {duration_seconds}s. Total: {total_count}. Outcomes: {outcomes}")

        # Optional Notion review push if Notion config is provided
        notion_push: Dict[str, Any] = {}
        check_ids = [f["check_id"] for f in flagged_schemes if f.get("check_id")]
        if check_ids and os.getenv("NOTION_API_TOKEN") and os.getenv("NOTION_CONTENT_CHECK_DATA_SOURCE_ID"):
            try:
                # If notion push helper is available
                from app.clients.notion_review import push_flagged
                notion_push = push_flagged(check_ids, db=db, now=now)
            except ImportError:
                logger.info("Notion push helper not imported; skipping Notion sync in job")
            except Exception as e:
                logger.error(f"Notion review push failed: {e}")
                notion_push = {"error": str(e)}

        return {
            "success": True,
            "total_checked": total_count,
            "outcomes": outcomes,
            "flagged_schemes": flagged_schemes,
            "failed_schemes": failed_schemes,
            "notion_push": notion_push,
            "duration_seconds": duration_seconds,
        }

    except Exception as e:
        logger.error(f"Cloud Run content check job failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Cloud Run Job: Monthly Scheme Content Check")
    parser.add_argument("--scheme-ids", nargs="*", help="Specific scheme IDs to process")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrent workers (default: 2)")
    args = parser.parse_args()

    result = run_job_core(scheme_ids=args.scheme_ids, concurrency=args.concurrency)
    print(json.dumps(result, indent=2, default=str))
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()

