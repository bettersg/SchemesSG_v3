"""Public response shapes for the partner API.

Every scheme leaving this API goes through ``to_public_scheme``. Scheme documents
carry internal fields — ``approved_by`` is a reviewer's email address,
``scraped_text`` is a raw source-page dump, ``source_entry_id`` points into
submission records — and new-scheme creation spreads a whole approval payload
into the document, so the stored field set is not fixed at write time. An
allowlist is therefore the only shape that is safe *and* stable: a field added
internally later cannot silently join the partner contract.
"""

from typing import Any


PUBLIC_FIELDS = (
    "scheme_id",
    "scheme",
    "description",
    "summary",
    "eligibility",
    "who_is_it_for",
    "what_it_gives",
    "scheme_type",
    "agency",
    "link",
    "address",
    "phone",
    "email",
    "service_area",
    "planning_area",
    "image",
    "status",
)


def to_public_scheme(doc_id: str | None, data: dict[str, Any]) -> dict[str, Any]:
    """Map an internal scheme document to the documented public shape.

    Args:
        doc_id: Firestore document ID, authoritative for ``scheme_id``.
        data: The internal scheme document.

    Returns:
        A dict containing exactly ``PUBLIC_FIELDS`` and nothing else.
    """
    public = {field: data.get(field) for field in PUBLIC_FIELDS}
    public["scheme_id"] = doc_id or data.get("scheme_id")
    return public


def error_body(code: str, message: str, **extras: Any) -> dict[str, Any]:
    """Build the standard partner error envelope.

    Args:
        code: Stable machine-readable error code.
        message: Human-readable explanation.
        **extras: Additional fields, e.g. ``merged_into`` for retired schemes.

    Returns:
        ``{"error": {"code": ..., "message": ..., **extras}}``
    """
    return {"error": {"code": code, "message": message, **extras}}
