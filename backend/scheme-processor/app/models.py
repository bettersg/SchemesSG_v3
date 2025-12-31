"""Pydantic models for API request/response."""

from typing import Optional

from pydantic import BaseModel


class ProcessRequest(BaseModel):
    """Request to process a new scheme submission."""

    doc_id: str
    scheme_name: str
    scheme_url: str
    original_data: dict = {}


class ProcessResponse(BaseModel):
    """Response from scheme processing."""

    success: bool
    doc_id: str
    status: str
    slack_ts: Optional[str] = None
    error: Optional[str] = None
