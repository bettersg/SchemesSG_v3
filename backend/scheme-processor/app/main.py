"""
Cloud Run Scheme Processor Service.

Full pipeline for processing new scheme submissions:
1. Scrape URL with crawl4ai + Playwright
2. Extract fields with Azure OpenAI LLM
3. Extract contacts with regex
4. Get planning area from OneMap API
5. Update Firestore with results
6. Post to Slack for human review

Also runs the monthly content-change check (/content-check, see app/content_check.py).
"""

import os

from app.clients.firestore import get_firestore_client
from app.content_check import ContentStore, check_scheme
from app.models import ContentCheckRequest, ContentCheckResponse, ContentCheckResult, ProcessRequest, ProcessResponse
from app.pipeline import process_scheme
from app.services.scraper import scrape_url
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel


app = FastAPI(
    title="Scheme Processor", description="Cloud Run service for processing new scheme submissions", version="0.1.0"
)


class HealthResponse(BaseModel):
    """Response body for /health endpoint."""

    status: str


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.post("/process", response_model=ProcessResponse)
async def process(request: ProcessRequest):
    """
    Process a new scheme submission.

    Runs the full pipeline:
    1. Scrape URL
    2. Extract fields with LLM
    3. Extract contacts with regex
    4. Get planning area
    5. Update Firestore
    6. Post to Slack
    """
    logger.info(f"Processing scheme: {request.doc_id} - {request.scheme_name}")

    try:
        result = await process_scheme(
            doc_id=request.doc_id,
            scheme_name=request.scheme_name,
            scheme_url=request.scheme_url,
            original_data=request.original_data,
            type_of_request=request.type_of_request,
            target_scheme_id=request.target_scheme_id,
        )
        return ProcessResponse(**result)

    except Exception as e:
        logger.error(f"Processing failed for {request.doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/content-check", response_model=ContentCheckResponse)
async def content_check(request: ContentCheckRequest):
    """
    Monthly content-change check for each scheme, one at a time: skip, scrape, then save a
    baseline or diff against the snapshot and flag out-of-date fields for review.
    One scheme failing doesn't stop the rest; it is reported as outcome "error".
    """
    db = get_firestore_client()
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore not configured")
    store = ContentStore(db)

    results = []
    for scheme_id in request.scheme_ids:
        try:
            results.append(ContentCheckResult(**await check_scheme(scheme_id, store, scrape_url)))
        except Exception as e:
            logger.exception(f"Content check failed for {scheme_id}")
            results.append(ContentCheckResult(scheme_id=scheme_id, outcome="error", detail=str(e)[:500]))
    return ContentCheckResponse(results=results)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
