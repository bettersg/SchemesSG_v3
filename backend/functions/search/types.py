from typing import Dict, List, Optional
from pydantic import BaseModel


class PredictParams(BaseModel):
    """Parameters for search model (sent by client)"""

    query: str
    top_k: Optional[int] = 20
    similarity_threshold: Optional[float] = None
    is_warmup: Optional[bool] = False  # Add flag for warmup requests


class PaginatedSearchParams(BaseModel):
    """Parameters for paginated search (sent by client)"""

    query: str
    limit: Optional[int] = 20
    cursor: Optional[str] = None
    similarity_threshold: Optional[float] = None
    is_warmup: Optional[bool] = False
    top_k: Optional[int] = 100  # Number of items to retrieve from vector search
    filters: Optional[Dict[str, List[str]]] = {}
