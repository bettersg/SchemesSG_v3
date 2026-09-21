"""Shared scheme lifecycle statuses and retirement validation."""

from collections.abc import Mapping
from typing import Any


RETIRED_STATUS = "retired"
NON_SEARCHABLE_STATUSES = frozenset({"inactive", RETIRED_STATUS})


def retirement_validation_error(
    target_scheme_id: str,
    merged_into: str | None,
    *,
    merge_target_exists: bool = True,
    merge_target_data: Mapping[str, Any] | None = None,
) -> str | None:
    """Return a retirement merge validation error, or ``None`` when valid."""
    if not merged_into:
        return None
    if merged_into == target_scheme_id:
        return "A retired scheme cannot be merged into itself"
    if not merge_target_exists or (merge_target_data or {}).get("status") == RETIRED_STATUS:
        return f"Merge target {merged_into!r} must exist and must not be retired"
    return None
