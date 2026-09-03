from typing import Optional
from pydantic import BaseModel


class PredictParams(BaseModel):
    """Parameters for the agent search tool"""

    query: str
    similarity_threshold: Optional[float] = None
    session_id: Optional[str] = None  # Add optional session_id for context association
    requested_target: Optional[int] = None  # count the user asked for, e.g. "20 healthcare schemes"
