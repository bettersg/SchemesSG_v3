"""
Link Discovery Agent Batch Job.

Scheduled function that:
1. Reads Firestore schemes with broken links detected by the link check script
   (status='inactive' or link_suspect=True)
2. Runs the link discovery agent (call_link_check_agent) for each scheme to find replacement URLs
3. Updates Firestore with discovered link information
4. Configurable concurrency parameter (max_parallel_jobs) to decide how many parallel jobs run at a time
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from browser_use import Agent, Browser, ChatAzureOpenAI
from fb_manager.firebaseManager import get_firestore_client
from firebase_functions import options, scheduler_fn
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl, field_validator
from utils.sitemap_discovery import discover_relevant_pages
from utils.notion_scheme_link_verification import publish_discovery_to_notion


class URLFinderAgentResponse(BaseModel):
    url: str | None = Field(
        default=None,
        description=(
            "Exactly one verified official HTTP(S) URL "
            "for the most specific scheme page, or null. "
            "Never return multiple URLs."
        ),
    )

    summary: str = Field(
        description=(
            "Brief explanation of what you tried and found, "
            "and why the URL was selected / no URL found. "
            "Do not include additional URLs."
        )
    )

    evidence_urls: list[str] = Field(
        default_factory=list,
        description=(
            "Supporting evidence URLs used to verify "
            "the scheme. These are not final URLs."
        ),
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None):
        if value is None:
            return None

        # Validate without exposing format='uri'
        # in the model's JSON schema.
        return str(HttpUrl(value))


def llm_client():
    # Get Azure config from environment
    azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_base = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_version = os.getenv("OPENAI_API_VERSION", "2025-01-01-preview")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5")

    if not azure_key or not azure_base:
        logger.warning("Azure OpenAI not configured, skipping LLM extraction")
        return None

    return ChatAzureOpenAI(
        model=deployment_name,
        api_key=azure_key,
        base_url=azure_base,
        api_version=azure_version,
        temperature=0.0,
        max_retry=3,
    )


async def _call_link_check_agent_async(
    scheme_name: str,
    previous_link: str,
    session_id: str,
) -> URLFinderAgentResponse:
    llm = llm_client()
    if not llm:
        return URLFinderAgentResponse(
            url=None,
            summary="Azure OpenAI not configured, skipping link discovery agent",
        )

    # Phase 1: Sitemap discovery.
    try:
        sitemap_result = await discover_relevant_pages(
            scheme_name=scheme_name,
            previous_link=previous_link,
            top_k=10,
        )
        candidates = sitemap_result.candidates
        sitemap_urls = sitemap_result.sitemap_urls
    except Exception as exc:
        logger.warning(f"Sitemap discovery failed for {scheme_name}: {exc}")
        candidates = []
        sitemap_urls = []

    candidate_text = "\n".join(
        f"- {url} (relevance score: {score:.1f})"
        for url, score in candidates
    )

    if not candidate_text:
        candidate_text = "No relevant sitemap candidates found."

    browser = Browser(headless=True)

    task = f"""
        You are a URL verification agent.

        Your task is to locate the CURRENT, WORKING, and RELEVANT
        official webpage for a specific scheme, programme, or service
        whose previous URL may be broken.

        Scheme / Programme: {scheme_name}
        Previous URL: {previous_link}

        SITEMAP DISCOVERY RESULTS

        Discovered sitemap files:
        {sitemap_urls}

        Potentially relevant pages:
        {candidate_text}

        OBJECTIVE

        Find a webpage that genuinely represents the specified
        scheme, programme, or service.

        Your priority is PRECISION over recall.
        A false positive is worse than returning None.

        Do not return the closest available page simply because
        the exact programme page cannot be found.

        DISCOVERY PROCEDURE

        1. Inspect the previous URL.
        - If accessible, verify that it contains relevant
            information about the specified programme.
        - If redirected, inspect the final destination.
        - Do not assume a redirect destination is relevant.

        2. Inspect relevant sitemap candidates.
        - Sitemap URLs are navigation hints, NOT evidence
            that the programme is currently available.
        - Inspect actual webpage content before accepting
            any candidate.

        3. If a candidate is a listing or directory page,
        follow relevant links to locate a programme-specific
        page.

        4. If sitemap candidates are insufficient, explore
        the organisation's website manually.
        - Navigate through relevant programme and service
            sections.
        - Inspect pages that may have renamed or reorganised
            the original programme.
        - Do not use Google or DuckDuckGo.

        5. If the organisation's website explicitly links to
        an official programme page on an external platform,
        such as Facebook, that page may be considered.
        Verify the relationship and relevance first.

        STRICT ACCEPTANCE CRITERIA

        A URL may ONLY be returned if ALL the following
        conditions are satisfied:

        A. ACCESSIBILITY
        - The destination loads successfully.
        - It is not a 404 page, error page, or inaccessible
            resource.
        - Redirects must resolve to a relevant working page.

        B. PROGRAMME IDENTITY
        - The page must explicitly identify the requested
            programme or clearly establish that it is the
            same programme under a new name.
        - Matching only the organisation's name is NOT
            sufficient.
        - Generic descriptions of similar services are
            NOT sufficient.
        - A programme's existence must not be inferred
            from the organisation's broader mission.

        C. PAGE RELEVANCE
        - The page must provide substantive information
            specifically about the requested programme.
        - Examples include its purpose, activities,
            services, eligibility, application process,
            participation details, or contact instructions
            specific to that programme.
        - A passing mention of the programme is NOT enough.
        - A page describing a different service offered
            by the same organisation is NOT acceptable.

        D. PAGE PURPOSE
        - The page must serve as an appropriate destination
            for someone seeking information about or access
            to the requested programme.
        - Prefer a dedicated programme or service page.
        - A broader page is acceptable ONLY if it contains
            a clearly identifiable, substantive section
            specifically about the requested programme.
        - A generic homepage, support landing page,
            organisation overview, or contact page is NOT
            an acceptable substitute merely because it
            belongs to the correct organisation.

        E. CURRENT VALIDITY
        - The page must not explicitly indicate that the
            programme has ended, been discontinued, or is
            no longer available.
        - Historical announcements and archived articles
            are not sufficient evidence of current availability.
        - Do not infer that a programme is active solely
            because an old page remains accessible.

        FALSE POSITIVE PREVENTION

        Reject candidates exhibiting any of these patterns:

        1. GENERIC LANDING PAGE
        The page offers general information about the
        organisation or its services but does not contain
        programme-specific information.

        2. INDIRECT ASSOCIATION
        The page discusses a related topic or service,
        but does not explicitly establish its connection
        to the requested programme.

        3. PASSING MENTION
        The programme name appears only incidentally,
        without substantive programme information.

        4. WRONG AUDIENCE OR PURPOSE
        The page is intended for a different activity,
        audience, or function and does not adequately
        describe or provide access to the programme.

        5. UNSUPPORTED REPLACEMENT
        The agent assumes that a broader service,
        department, or programme has replaced the
        requested programme without explicit evidence.

        6. HISTORICAL EVIDENCE
        The candidate is supported only by outdated
        references, previous URLs, or historical content.

        IMPORTANT REASONING RULES

        - Do not equate "related" with "equivalent".
        - Do not equate "mentioned" with "represented".
        - Do not equate "official domain" with "correct page".
        - Do not assume a generic support page covers a
        discontinued or missing programme.
        - Do not assume a programme has been renamed or
        absorbed into another service without evidence.
        - Do not fabricate explanations to justify a
        weakly related URL.
        - A high sitemap relevance score does not override
        the acceptance criteria.
        - If a candidate fails any mandatory criterion,
        reject it and continue searching.

        FINAL VERIFICATION

        Before returning a URL, explicitly check:

        1. Does the final URL load successfully?
        2. Does the page clearly identify the requested
        programme or an explicitly established successor?
        3. Does it contain substantive information about
        that programme?
        4. Does the page contain any links to a more specific
        page dedicated to the requested programme?
        - Thoroughly inspect the page for relevant links,
            subpages, or references that may lead to a more
            specific programme page.
        - If such a link is found, return to the exploration
            stage and navigate to that page.
        - Repeat this process until no further relevant,
            more specific pages can be found.
        - Only return the current page if no more specific
            and suitable programme page is available.

        If any answer is NO or cannot be verified,
        do not return that URL. For check 4, if a potentially more specific page is
        found, resume exploration and verify that page before
        making a final decision. Do not return a broader page
        without first investigating its more specific links.

        OUTPUT REQUIREMENTS

        If a qualifying URL is found:
        - Return the exact final working URL.
        - Summarise the programme-specific information
        found on that page.
        - Explain briefly why it is a valid replacement.
        - Do not claim that the page is a replacement
        unless the evidence supports that conclusion.

        If no qualifying URL is found:
        - Return url=None.
        - Summarise the pages investigated.
        - Explain why the closest candidates were rejected.
        - Clearly distinguish between:
        (a) Programme confirmed discontinued.
        (b) Programme not found or current status unknown.

        Never return a weakly related page merely to
        produce a successful result.

        When evidence is insufficient, return None.
        """

    try:
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            output_model_schema=URLFinderAgentResponse,
        )

        history = await agent.run()

        response = history.structured_output

        if response is None:
            final_text = history.final_result() or ""

            try:
                response = (
                    URLFinderAgentResponse.model_validate_json(
                        final_text
                    )
                )
            except Exception:
                response = URLFinderAgentResponse(
                    url=None,
                    summary=final_text,
                )

        return response

    finally:
        try:
            await browser.close()
        except Exception:
            logger.exception(
                f"Session {session_id} | Failed to close browser"
            )


def call_link_check_agent(
    scheme_name: str,
    previous_link: str,
    session_id: str,
) -> URLFinderAgentResponse:
    """
    Synchronous entry point to run the link discovery agent for a scheme.

    Args:
        scheme_name: Name of the scheme or programme
        previous_link: Previous (potentially dead) URL
        session_id: Unique session identifier for logging/tracing

    Returns:
        URLFinderAgentResponse with discovered URL and summary
    """
    coro = _call_link_check_agent_async(
        scheme_name=scheme_name,
        previous_link=previous_link,
        session_id=session_id,
    )
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


# Expose async variant if needed
call_link_check_agent_async = _call_link_check_agent_async


def check_single_scheme(
    doc_id: str,
    scheme_data: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], URLFinderAgentResponse | None]:
    """
    Run link discovery agent on a single scheme.

    Args:
        doc_id: Firestore document ID
        scheme_data: Scheme document data

    Returns:
        Tuple of (doc_id, scheme_data, result)
    """
    scheme_name = scheme_data.get("scheme", "") or scheme_data.get("scheme_name", "") or "Unknown"
    previous_link = scheme_data.get("link", "")
    session_id = f"discovery-{doc_id}"

    result = call_link_check_agent(
        scheme_name=scheme_name,
        previous_link=previous_link,
        session_id=session_id,
    )
    return (doc_id, scheme_data, result)


def run_link_discovery_core(
    db=None,
    max_parallel_jobs: int = 3,
    update_db: bool = True,
    publish_to_notion: bool = True,
) -> Dict[str, Any]:
    """
    Core synchronous logic for running link discovery agent on broken links.

    This function can be called directly for local testing or from the scheduled function.

    Args:
        db: Firestore client (optional, will create if not provided)
        max_parallel_jobs: Number of parallel jobs to run at a time (default: 3)
        update_db: Whether to write discovered URLs back to Firestore (default: True)

    Returns:
        Dict with results summary
    """
    start_time = time.time()
    logger.info("Starting link discovery batch job...")

    try:
        if db is None:
            db = get_firestore_client()

        # Step 1: Fetch schemes with broken links from Firestore (filter those processed before)
        logger.info("Fetching schemes with broken links from Firestore...")
        schemes_ref = db.collection("schemes")
        discoveries_ref = db.collection("link_discoveries")

        # Fetch existing discovery document IDs
        logger.info("Fetching previously investigated schemes...")

        existing_discovery_ids = {
            doc.id
            for doc in discoveries_ref.select([]).stream()
        }

        logger.info(
            f"Found {len(existing_discovery_ids)} previously investigated schemes"
        )

        docs = schemes_ref.stream()

        schemes_to_check: List[Tuple[str, Dict[str, Any]]] = []
        inactive_count = 0
        suspect_count = 0
        retired_count = 0
        skipped_count = 0

        for doc in docs:
            data = doc.to_dict()
            if data.get("status") == "retired":
                retired_count += 1
                continue

            is_inactive = data.get("status") == "inactive"

            if is_inactive:
                inactive_count += 1
                if doc.id in existing_discovery_ids:
                    skipped_count += 1
                    logger.debug(
                        f"Skipping previously investigated scheme: "
                        f"{data.get('scheme', 'Unknown')} ({doc.id})"
                    )
                    continue
                schemes_to_check.append((doc.id, data))

        total_count = len(schemes_to_check)
        logger.info(
            f"Found {total_count} schemes with broken links to investigate "
            f"({inactive_count} inactive, {suspect_count} suspect, {retired_count} retired, {skipped_count} skipped)"
        )

        if total_count == 0:
            duration_seconds = round(time.time() - start_time, 2)
            return {
                "success": True,
                "discovery": {
                    "total_checked": 0,
                    "found_count": 0,
                    "not_found_count": 0,
                    "error_count": 0,
                    "skipped_count": 0,
                    "found_links": [],
                    "not_found_links": [],
                },
                "duration_seconds": duration_seconds,
            }

        # Step 2: Run discovery agent with concurrency parameter
        found_count = 0
        not_found_count = 0
        error_count = 0
        found_links: List[Dict[str, Any]] = []
        not_found_links: List[Dict[str, Any]] = []
        discovery_results: List[Tuple[str, Dict[str, Any], URLFinderAgentResponse | None]] = []

        max_workers = max(1, min(max_parallel_jobs, total_count))
        logger.info(f"Running link discovery with {max_workers} parallel workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(check_single_scheme, doc_id, data): (doc_id, data)
                for doc_id, data in schemes_to_check
            }

            for future in as_completed(futures):
                doc_id, scheme_data = futures[future]
                try:
                    _, _, result = future.result()
                    discovery_results.append((doc_id, scheme_data, result))

                    if result and getattr(result, "url", None):
                        found_count += 1
                        found_links.append(
                            {
                                "doc_id": doc_id,
                                "scheme_name": scheme_data.get("scheme", "Unknown"),
                                "previous_link": scheme_data.get("link", ""),
                                "discovered_url": str(result.url),
                                "summary": result.summary,
                                "evidence_urls": result.evidence_urls,
                            }
                        )
                    else:
                        not_found_count += 1
                        not_found_links.append(
                            {
                                "doc_id": doc_id,
                                "scheme_name": scheme_data.get("scheme", "Unknown"),
                                "previous_link": scheme_data.get("link", ""),
                                "summary": result.summary if result else "No URL found",
                            }
                        )
                except Exception as e:
                    logger.error(f"Error checking scheme {doc_id}: {e}")
                    error_count += 1
                    discovery_results.append((doc_id, scheme_data, None))

        logger.info(
            f"Link discovery complete: {found_count} URLs found, "
            f"{not_found_count} not found, {error_count} errors, {skipped_count} skipped"
        )

        # Step 3: Update Firestore if enabled
        if update_db:
            logger.info("Updating Firestore with discovery results...")
            batch = db.batch()
            batch_count = 0
            now_iso = datetime.now(timezone.utc).isoformat()

            for doc_id, scheme_data, result in discovery_results:
                discovery_ref = discoveries_ref.document(doc_id)
                batch.set(
                    discovery_ref,
                    {
                        "scheme_id": doc_id,
                        "scheme_name": scheme_data.get("scheme"),
                        "previous_link": scheme_data.get("link"),
                        "discovered_link": str(result.url) if result else None,
                        "summary": result.summary if result else None,
                        "evidence_urls": result.evidence_urls if result else [],
                        "checked_at": now_iso,
                    },
                )
                batch_count += 1

                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0

            if batch_count > 0:
                batch.commit()

            logger.info("Firestore updates complete")

        # Step 4: Publish discovery results to Notion
        notion_result = None

        if publish_to_notion:
            logger.info("Publishing link discovery results to Notion...")

            try:
                notion_result = publish_discovery_to_notion(
                    found_links=found_links,
                    not_found_links=not_found_links,
                )

                logger.info(
                    "Notion publishing complete: "
                    f"{notion_result['published_count']} published, "
                    f"{notion_result['failed_count']} failed"
                )

            except Exception as exc:
                logger.exception(f"Notion publishing failed: {exc}")

                notion_result = {
                    "total": len(found_links) + len(not_found_links),
                    "published_count": 0,
                    "failed_count": len(found_links) + len(not_found_links),
                    "error": str(exc),
                }

        # return summary of results
        duration_seconds = round(time.time() - start_time, 2)
        response_data = {
            "success": True,
            "discovery": {
                "total_checked": total_count,
                "found_count": found_count,
                "not_found_count": not_found_count,
                "error_count": error_count,
                "skipped_count": skipped_count,
                "found_links": found_links,
                "not_found_links": not_found_links,
            },
            "notion": notion_result,
            "duration_seconds": duration_seconds,
        }

        logger.info(f"Batch job complete in {duration_seconds}s")
        return response_data

    except Exception as e:
        logger.error(f"Batch job failed: {e}")
        return {"success": False, "error": str(e)}


@scheduler_fn.on_schedule(
    schedule="0 10 * * 1",  # Run at 10am every Monday (after 9am link check)
    region="asia-southeast1",
    memory=options.MemoryOption.GB_2,
    timeout_sec=540,  # 9 minutes max
    retry_count=1,
)
def scheduled_link_discovery_agent(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Weekly scheduled function for discovering working links for broken schemes.

    Runs every Monday at 10am SGT.
    Queries schemes with broken links and executes the link discovery agent.

    Args:
        event: Scheduled event object from Firebase
    """
    logger.info(f"Scheduled link discovery job triggered at {event.schedule_time}")
    result = run_link_discovery_core()
    logger.info(f"Scheduled link discovery result: {json.dumps(result, default=str)}")


# Alias for convenience
scheduled_link_discovery = scheduled_link_discovery_agent
