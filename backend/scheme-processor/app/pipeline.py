"""
Scheme Processing Pipeline.

Orchestrates scraping, LLM extraction, and Slack posting.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from loguru import logger

from app.services.scraper import scrape_url
from app.services.llm_extractor import extract_with_llm
from app.services.extraction import extract_contacts
from app.clients.onemap import PlanningAreaService
from app.clients.slack_poster import post_to_slack_for_review
from app.clients.firestore import update_scheme_entry, get_firestore_client


async def process_scheme(
    doc_id: str,
    scheme_name: str,
    scheme_url: str,
    original_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run full processing pipeline for a scheme submission.

    Steps:
    1. Scrape URL
    2. Extract fields with LLM
    3. Extract contacts with regex
    4. Get planning area from address
    5. Update Firestore
    6. Post to Slack

    Returns:
        Dict with success, doc_id, status, slack_ts, error
    """
    logger.info(f"Starting pipeline for: {doc_id}")

    result = {
        "success": False,
        "doc_id": doc_id,
        "status": "processing",
        "slack_ts": None,
        "error": None
    }

    # Get Firestore client
    db = get_firestore_client()

    # Update status to processing
    update_scheme_entry(db, doc_id, {
        "pipeline_status": "processing",
        "pipeline_started_at": datetime.now(timezone.utc).isoformat()
    })

    try:
        # Step 1: Scrape URL
        logger.info(f"Step 1: Scraping {scheme_url}")
        scrape_result = await scrape_url(scheme_url)

        scraped_text = scrape_result.get("content", "")
        images = scrape_result.get("images", [])
        logo_url = scrape_result.get("logo_url")

        if scrape_result.get("error"):
            logger.warning(f"Scrape warning for {doc_id}: {scrape_result['error']}")

        # Step 2: Extract fields with LLM
        llm_fields = {}
        if scraped_text and len(scraped_text) > 500:
            logger.info(f"Step 2: Extracting fields with LLM ({len(scraped_text)} chars)")
            llm_fields = await extract_with_llm(scraped_text)

        # Step 3: Extract contacts with regex (more reliable than LLM)
        if scraped_text:
            logger.info(f"Step 3: Extracting contacts with regex")
            contacts = extract_contacts(scraped_text)
            if contacts.emails:
                llm_fields["email"] = ", ".join(contacts.emails)
            if contacts.phones:
                llm_fields["phone"] = ", ".join(contacts.phones)

        # Step 4: Get planning area from address
        planning_area = "No Location"
        address = llm_fields.get("address")
        if address:
            logger.info(f"Step 4: Getting planning area for address")
            try:
                planning_service = PlanningAreaService()
                planning_area = planning_service.get_planning_area(address) or "No Location"
            except Exception as e:
                logger.warning(f"Planning area extraction failed: {e}")

        # Prepare processed data
        processing_status = "completed"
        error_msg = None

        if scrape_result.get("error"):
            error_msg = scrape_result["error"]
            if "MANUAL_REVIEW" in error_msg:
                processing_status = "needs_review"
            elif "Error" in error_msg:
                processing_status = "scraping_failed"

        processed_data = {
            "doc_id": doc_id,
            "scheme_name": scheme_name,
            "scheme_url": scheme_url,
            "scraped_text": scraped_text,
            "llm_fields": llm_fields,
            "planning_area": planning_area,
            "logo_url": logo_url,
            "original_data": original_data,
            "processing_status": processing_status,
            "error": error_msg
        }

        # Step 5: Update Firestore
        logger.info(f"Step 5: Updating Firestore for {doc_id}")
        update_scheme_entry(db, doc_id, {
            "pipeline_status": processing_status,
            "pipeline_completed_at": datetime.now(timezone.utc).isoformat(),
            "scraped_text": scraped_text,
            "llm_fields": llm_fields,
            "planning_area": planning_area,
            "logo_url": logo_url,
            "pipeline_error": error_msg
        })

        # Step 6: Post to Slack
        logger.info(f"Step 6: Posting to Slack for {doc_id}")
        slack_result = post_to_slack_for_review(doc_id, processed_data, db)

        result["success"] = True
        result["status"] = processing_status
        result["slack_ts"] = slack_result.get("ts") if slack_result else None

        logger.info(f"Pipeline completed for {doc_id}")
        return result

    except Exception as e:
        logger.error(f"Pipeline error for {doc_id}: {e}")
        import traceback
        traceback.print_exc()

        # Update Firestore with error status
        try:
            update_scheme_entry(db, doc_id, {
                "pipeline_status": "failed",
                "pipeline_error": str(e),
                "pipeline_failed_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

        result["status"] = "failed"
        result["error"] = str(e)
        return result
