"""Small structured latency logger shared by the agent search path."""

import json
from time import perf_counter
from typing import Any


def log_elapsed(logger: Any, trace_id: str | None, stage: str, started_at: float, **details: Any) -> float:
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "latency_trace trace_id={} stage={} duration_ms={} details={}",
        trace_id or "unknown",
        stage,
        duration_ms,
        json.dumps(details, sort_keys=True, separators=(",", ":")),
    )
    return duration_ms
