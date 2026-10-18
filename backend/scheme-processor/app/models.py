"""Pydantic models for API request/response."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Request to process a new scheme submission."""

    doc_id: str
    scheme_name: str
    scheme_url: str
    original_data: dict = {}
    type_of_request: Literal["new", "update"] = "new"
    target_scheme_id: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response from scheme processing."""

    success: bool
    doc_id: str
    status: str
    slack_ts: Optional[str] = None
    error: Optional[str] = None


class ContentCheckRequest(BaseModel):
    """Request to run the monthly content check (issue #407) on a few schemes."""

    # A handful per call: each scrape runs a browser and the caller times out at 5 minutes.
    scheme_ids: List[str] = Field(min_length=1, max_length=10)


class ContentCheckResult(BaseModel):
    """What happened to one scheme."""

    scheme_id: str
    outcome: Literal["not_found", "skipped", "scrape_failed", "baseline", "unchanged", "flagged", "error"]
    detail: Optional[str] = None
    check_id: Optional[str] = None


class ContentCheckResponse(BaseModel):
    """Response from /content-check, one result per requested scheme, in request order."""

    results: List[ContentCheckResult]
