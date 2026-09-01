"""The partner API contract surface: request parsing in, response shapes out.

Every scheme leaving this API goes through ``to_public_scheme``. Scheme documents
carry internal fields — ``approved_by`` is a reviewer's email address,
``scraped_text`` is a raw source-page dump, ``source_entry_id`` points into
submission records — and new-scheme creation spreads a whole approval payload
into the document, so the stored field set is not fixed at write time. An
allowlist is therefore the only shape that is safe *and* stable: a field added
internally later cannot silently join the partner contract.

``PartnerRequestError`` and ``clamp_limit`` live here rather than in their own
modules because both ``partner/api.py`` and ``partner/search.py`` already import
this module, so there is no cycle and no third file to keep in step.
"""

from typing import Any


MAX_LIMIT = 50


class PartnerRequestError(Exception):
    """A client mistake whose message was written here and is safe to return.

    The handler used to catch bare ``ValueError`` and echo ``str(exc)`` into the
    400 body. That reads fine while every ValueError is one we raised, but the
    partner call path also runs Firestore, pandas and the shared catalog helpers —
    any ValueError from those would have had its internal message, and whatever
    field names or paths it mentions, handed to a partner verbatim. CodeQL flagged
    the same flow as stack-trace exposure.

    So: intentional client errors raise this, everything else is a logged 500.
    ``client_message`` is the literal we authored, kept as an explicit attribute
    so nothing has to stringify an exception to build a response.
    """

    def __init__(self, client_message: str):
        super().__init__(client_message)
        self.client_message = client_message


def clamp_limit(raw: Any, *, default: int, maximum: int = MAX_LIMIT) -> int:
    """Clamp a requested page size into ``1..maximum``.

    ``default`` differs per operation — list follows the catalog's page size,
    search uses its own — so it is passed in rather than baked in here.

    Raises:
        PartnerRequestError: If ``raw`` is present but not an integer.
    """
    if raw is None:
        return default
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise PartnerRequestError("'limit' must be an integer") from None
    return max(1, min(limit, maximum))


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
