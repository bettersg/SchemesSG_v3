"""Partner API key verification and per-partner rate limiting.

Deliberately separate from ``utils/auth.py``. That module gates the frontend's
anonymous Firebase tokens and is called from seven endpoints, two of which write
data or spend LLM budget. Adding a partner branch there would hand every partner
key access to all seven, so partner identity lives in its own collection with its
own gate.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud.firestore_v1 import Increment


PARTNER_KEYS_COLLECTION = "partner_keys"
RATE_LIMIT_COLLECTION = "partner_rate_limits"

API_KEY_HEADER = "X-API-Key"
# 600/min (10 req/s). Partners are hand-vetted and each key is issued by a
# maintainer, so this is not an abuse control — it is a blast-radius guard so a
# buggy retry loop on a partner's side can't quietly run up Firestore reads and
# 2GB function instances. Generous enough that a page fanning out several scheme
# lookups per view never notices it.
DEFAULT_RATE_LIMIT_PER_MIN = 600

# Counter docs are only meaningful for their own minute. Firestore TTL on this
# field reaps them; see docs/partner-api-runbook.md.
COUNTER_TTL = timedelta(minutes=10)

@dataclass(frozen=True)
class AuthError:
    """A rejected key, already carrying its code, message and HTTP status.

    One object rather than parallel code→status and code→message maps, and it
    mirrors ``partner.routing.RouteError`` so both gates answer the same shape.
    """

    code: str
    message: str
    status: int


@dataclass(frozen=True)
class PartnerIdentity:
    """A verified partner and the budget their key grants."""

    consumer: str
    rate_limit_per_min: int


# A revoked key is 403 rather than 401 so a partner can tell "you were turned off"
# from "we've never seen this key".
MISSING_KEY = AuthError("missing_key", f"Missing {API_KEY_HEADER} header", 401)
INVALID_KEY = AuthError("invalid_key", "Unrecognised API key", 401)
REVOKED_KEY = AuthError("revoked_key", "This API key has been revoked", 403)


def hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest used as the ``partner_keys`` document ID.

    Raw keys are never stored, so a database leak does not leak usable keys.
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _header(req: Any, name: str) -> str | None:
    # ponytail: werkzeug headers are already case-insensitive; the lowercase
    # retry only exists so plain dicts (tests, local harnesses) work too.
    return req.headers.get(name) or req.headers.get(name.lower())


def verify_partner_key(req: Any, db: Any) -> PartnerIdentity | AuthError:
    """Verify the ``X-API-Key`` header against the ``partner_keys`` collection.

    Args:
        req: The incoming request.
        db: Firestore client.

    Returns:
        A ``PartnerIdentity`` when the key is good, otherwise an ``AuthError``
        carrying the code, message and status to return.
    """
    raw_key = _header(req, API_KEY_HEADER)
    if not raw_key:
        return MISSING_KEY

    doc = db.collection(PARTNER_KEYS_COLLECTION).document(hash_key(raw_key)).get()
    if not doc.exists:
        return INVALID_KEY

    data = doc.to_dict() or {}
    # Strict `is True`, not truthiness: revocation is done by hand in the Firestore
    # console (see the runbook), where `active` can end up as the *string*
    # "false" — which is truthy and would keep a revoked key working.
    if data.get("active") is not True:
        return REVOKED_KEY

    # `or` would turn a deliberate 0 into the default, un-throttling a partner
    # that was throttled to zero as a softer alternative to revoking.
    configured = data.get("rate_limit_per_min")
    try:
        limit = DEFAULT_RATE_LIMIT_PER_MIN if configured is None else int(configured)
    except (TypeError, ValueError):
        # Hand-edited junk in the console shouldn't 500 the partner's request.
        limit = DEFAULT_RATE_LIMIT_PER_MIN
    return PartnerIdentity(consumer=data.get("consumer", ""), rate_limit_per_min=max(limit, 0))


def check_and_increment_rate_limit(db: Any, consumer: str, limit_per_min: int) -> tuple[bool, int]:
    """Consume one request from a partner's per-minute budget.

    One budget per partner, shared across every operation — spending it on a list
    call also exhausts search.

    Args:
        db: Firestore client.
        consumer: Partner identifier from the key document.
        limit_per_min: Requests allowed per minute for this partner.

    Returns:
        ``(allowed, remaining)``.
    """
    now = datetime.now(tz=timezone.utc)
    bucket = now.strftime("%Y%m%d%H%M")
    doc_ref = db.collection(RATE_LIMIT_COLLECTION).document(f"{consumer}:{bucket}")

    # ponytail: increment-then-read, so a burst racing across instances can
    # overshoot by roughly the number of concurrent requests. Move to a
    # transaction if a partner ever fans out enough for that to matter.
    doc_ref.set(
        {"count": Increment(1), "consumer": consumer, "expires_at": now + COUNTER_TTL},
        merge=True,
    )
    count = int((doc_ref.get().to_dict() or {}).get("count") or 1)

    return count <= limit_per_min, max(limit_per_min - count, 0)
