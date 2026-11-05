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
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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


MAX_ITEMS_PER_BLOCK = 10
SLACK_MAX_BLOCKS = 50


def get_slack_client() -> WebClient:
    """Get Slack WebClient instance."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN not set")
    return WebClient(token=bot_token)


def get_slack_channel() -> str:
    """Get Slack channel ID for notifications."""
    channel = os.getenv("SLACK_CHANNEL_ID")
    if not channel:
        raise ValueError("SLACK_CHANNEL_ID not set")
    return channel


def _format_flagged_scheme(item: Dict[str, Any]) -> str:
    doc_id = item.get("doc_id", "Unknown")
    name = item.get("scheme_name") or doc_id
    detail = item.get("detail", "Content changes detected")
    check_id = item.get("check_id")
    check_str = f" (`{check_id}`)" if check_id else ""
    return f"• *{name}*{check_str}\n  ID: `{doc_id}`\n  Detail: _{detail}_"


def _format_failed_scheme(item: Dict[str, Any]) -> str:
    doc_id = item.get("doc_id", "Unknown")
    name = item.get("scheme_name") or doc_id
    outcome = item.get("outcome", "error")
    detail = item.get("detail", "Unknown error")
    return f"• *{name}*\n  ID: `{doc_id}`\n  Outcome: `{outcome}`\n  Error: _{detail}_"


def _chunked_blocks(items: List[Dict[str, Any]], formatter: Callable[[Dict[str, Any]], str]) -> List[dict]:
    """Group items into Slack section blocks, up to MAX_ITEMS_PER_BLOCK per block."""
    blocks = []
    for i in range(0, len(items), MAX_ITEMS_PER_BLOCK):
        chunk = items[i : i + MAX_ITEMS_PER_BLOCK]
        text = "\n".join(formatter(item) for item in chunk)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
    return blocks


def _enforce_block_cap(blocks: List[dict]) -> List[dict]:
    """Truncate blocks to Slack's 50-block limit, adding an overflow notice if truncated."""
    if len(blocks) <= SLACK_MAX_BLOCKS:
        return blocks
    omitted = len(blocks) - (SLACK_MAX_BLOCKS - 1)
    truncated = blocks[: SLACK_MAX_BLOCKS - 1]
    truncated.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":warning: _… and {omitted} more entries omitted. Check logs for the full list._",
                }
            ],
        }
    )
    return truncated


def build_content_check_summary_message(
    results_summary: Dict[str, Any],
    flagged_schemes: List[Dict[str, Any]],
    failed_schemes: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Build Slack message summarizing monthly scheme content check results.

    Args:
        results_summary: Content check summary statistics
        flagged_schemes: List of flagged schemes with change details
        failed_schemes: List of schemes that failed checking

    Returns:
        Slack message payload with blocks
    """
    total_checked = results_summary.get("total_checked", 0)
    outcomes = results_summary.get("outcomes", {})
    unchanged_count = outcomes.get("unchanged", 0)
    flagged_count = outcomes.get("flagged", 0)
    baseline_count = outcomes.get("baseline", 0)
    skipped_count = outcomes.get("skipped", 0)
    scrape_failed_count = outcomes.get("scrape_failed", 0)
    error_count = outcomes.get("error", 0)
    duration = results_summary.get("duration_seconds", 0)

    # Format duration nicely
    if duration >= 60:
        duration_str = f"{duration / 60:.1f} minutes"
    else:
        duration_str = f"{duration:.0f} seconds"

    summary_text = (
        f"*Summary:*\n"
        f"Total schemes checked: *{total_checked}*\n"
        f":white_check_mark: Unchanged: *{unchanged_count}*\n"
        f":warning: Flagged for review: *{flagged_count}*\n"
        f":new: Baseline snapshots: *{baseline_count}*\n"
        f":fast_forward: Skipped: *{skipped_count}*\n"
    )
    total_failures = scrape_failed_count + error_count
    if total_failures > 0:
        summary_text += f":x: Failures / Scrape errors: *{total_failures}*\n"
    summary_text += f":stopwatch: Duration: *{duration_str}*"

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Monthly Scheme Content Check Complete", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary_text}},
    ]

    # Add flagged schemes section if any
    if flagged_schemes:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Flagged Schemes ({len(flagged_schemes)}) - content changes detected:*"},
            }
        )
        blocks.extend(_chunked_blocks(flagged_schemes, _format_flagged_scheme))
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": ":eyes: Pending review rows created in `contentChecks`"}],
            }
        )

    fallback_text = f"Content Check Complete: {total_checked} checked, {flagged_count} flagged"
    if total_failures > 0:
        fallback_text += f", {total_failures} failed"

    return {
        "text": fallback_text,
        "blocks": _enforce_block_cap(blocks),
        "unfurl_links": False,
        "unfurl_media": False,
    }


def build_content_check_error_message(error: str) -> dict:
    """Build Slack message for content check failure."""
    return {
        "text": f"Content Check Failed: {error}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Content Check Failed", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f":x: *Error:* {error}"}},
        ],
    }


def run_job_core(
    db=None,
    store: Optional[ContentStore] = None,
    scheme_ids: Optional[List[str]] = None,
    concurrency: int = 2,
    now: Optional[datetime] = None,
    slack_client: Optional[WebClient] = None,
    slack_channel: Optional[str] = None,
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
                    scheme_name = res.get("scheme_name") or doc_id
                    if outcome == "flagged":
                        flagged_schemes.append(
                            {
                                "doc_id": doc_id,
                                "scheme_name": scheme_name,
                                "check_id": res.get("check_id"),
                                "detail": res.get("detail"),
                            }
                        )
                    elif outcome in ("scrape_failed", "error"):
                        failed_schemes.append(
                            {
                                "doc_id": doc_id,
                                "scheme_name": scheme_name,
                                "outcome": outcome,
                                "detail": res.get("detail"),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error checking scheme {doc_id}: {e}")
                    outcomes["error"] = outcomes.get("error", 0) + 1
                    failed_schemes.append({"doc_id": doc_id, "scheme_name": doc_id, "outcome": "error", "detail": str(e)})

        duration_seconds = round(time.time() - start_time, 2)
        logger.info(f"Content check complete in {duration_seconds}s. Total: {total_count}. Outcomes: {outcomes}")

        # Post summary to Slack
        logger.info("Posting summary to Slack...")
        try:
            client = slack_client or get_slack_client()
            channel = slack_channel or get_slack_channel()

            results_summary = {
                "total_checked": total_count,
                "outcomes": outcomes,
                "duration_seconds": duration_seconds,
            }

            message = build_content_check_summary_message(
                results_summary, flagged_schemes, failed_schemes
            )

            client.chat_postMessage(channel=channel, **message)
            logger.info("Slack notification sent")

        except (SlackApiError, ValueError) as e:
            logger.error(f"Failed to send Slack notification: {e}")

        return {
            "success": True,
            "total_checked": total_count,
            "outcomes": outcomes,
            "flagged_schemes": flagged_schemes,
            "failed_schemes": failed_schemes,
            "duration_seconds": duration_seconds,
        }

    except Exception as e:
        logger.error(f"Cloud Run content check job failed: {e}")

        # Try to send error notification to Slack
        try:
            client = slack_client or get_slack_client()
            channel = slack_channel or get_slack_channel()
            error_message = build_content_check_error_message(str(e))
            client.chat_postMessage(channel=channel, **error_message)
        except Exception:
            pass

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

