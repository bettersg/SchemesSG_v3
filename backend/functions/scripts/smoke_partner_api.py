"""
End-to-end smoke test for the partner API against a running local emulator.

Seeds three temporary partner keys, exercises every operation and every documented
failure mode over real HTTP, prints a pass/fail table, then deletes what it made.

The keys are deliberately separate. The per-minute budget is shared across
operations and is spent even by 4xx routing checks, so a single small-budget key
would 429 the functional checks and report failures against a correct API.
Instead the functional key gets generous headroom and throttling is proved on its
own key under its own consumer.

Refuses to run outside the dev project unless `--allow-project` names the target,
because seeding writes real `partner_keys` documents.

Prerequisites:
    cd backend && docker compose -f docker-compose-firebase.yml up --build

Usage:
    cd backend/functions
    uv run python scripts/smoke_partner_api.py
    uv run python scripts/smoke_partner_api.py --json ../../.evidence/smoke.json
    uv run python scripts/smoke_partner_api.py --keep-key   # leave the keys for manual poking
"""

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from typing import Any, Callable

import requests
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
from partner.serializers import PUBLIC_FIELDS
from utils.partner_auth import PARTNER_KEYS_COLLECTION, RATE_LIMIT_COLLECTION, hash_key
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES


DEFAULT_BASE = "http://127.0.0.1:5001/schemessg-v3-dev/asia-southeast1/partner_api"
SMOKE_CONSUMER = "smoke-test"
THROTTLE_CONSUMER = f"{SMOKE_CONSUMER}-throttle"
REVOKED_CONSUMER = f"{SMOKE_CONSUMER}-revoked"

# The per-minute budget is shared across operations and is spent by 4xx routing
# checks too, so the functional key needs enough headroom for the whole run.
# Throttling is proved on its own key, under its own consumer, so exhausting that
# budget cannot make the functional checks fail.
FUNCTIONAL_RATE_LIMIT = 200
THROTTLE_RATE_LIMIT = 3

# Seeding writes real key documents, so refuse anything that isn't the dev
# project unless the operator names the project explicitly.
DEV_PROJECT_IDS = {"schemessg-v3-dev"}

LEAKY_FIELDS = ("approved_by", "scraped_text", "source_entry_id", "search_booster")

results: list[dict[str, Any]] = []


def check(name: str, fn: Callable[[], str]) -> None:
    """Run one assertion, recording pass/fail rather than aborting the run."""
    try:
        detail = fn()
        results.append({"check": name, "ok": True, "detail": detail})
        print(f"  PASS  {name}\n        {detail}")
    except AssertionError as exc:
        results.append({"check": name, "ok": False, "detail": str(exc)})
        print(f"  FAIL  {name}\n        {exc}")
    except Exception as exc:  # noqa: BLE001 - a smoke run should report, not explode
        results.append({"check": name, "ok": False, "detail": f"{type(exc).__name__}: {exc}"})
        print(f"  ERROR {name}\n        {type(exc).__name__}: {exc}")


def get_firestore_client():
    """Initialise Firebase Admin from functions/.env under a named app."""
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)
    private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": os.getenv("FB_TYPE"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI"),
            "token_uri": os.getenv("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        }
    )
    try:
        app = initialize_app(cred, name="partner-smoke")
    except ValueError:
        app = None
    return firestore.client(app) if app else firestore.client()


def seed_key(db, consumer: str, rate_limit: int, *, active: bool = True) -> str:
    """Create a temporary key and clear any stale rate-limit buckets for it."""
    raw_key = f"sk_smoke_{secrets.token_urlsafe(24)}"
    db.collection(PARTNER_KEYS_COLLECTION).document(hash_key(raw_key)).set(
        {
            "consumer": consumer,
            "active": active,
            "created_at": datetime.now(tz=timezone.utc),
            "rate_limit_per_min": rate_limit,
        }
    )
    _clear_buckets(db, consumer)
    return raw_key


def _clear_buckets(db, consumer: str) -> None:
    for doc in db.collection(RATE_LIMIT_COLLECTION).where("consumer", "==", consumer).stream():
        doc.reference.delete()


def cleanup(db, raw_keys: list[str]) -> None:
    """Delete every document this run created. Safe to call twice."""
    for raw_key in raw_keys:
        db.collection(PARTNER_KEYS_COLLECTION).document(hash_key(raw_key)).delete()
    for consumer in (SMOKE_CONSUMER, THROTTLE_CONSUMER, REVOKED_CONSUMER):
        _clear_buckets(db, consumer)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the partner API against a local emulator.")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"Function base URL (default: {DEFAULT_BASE})")
    parser.add_argument("--json", dest="json_out", help="Write a JSON report to this path")
    parser.add_argument("--keep-key", action="store_true", help="Do not delete the seeded key")
    parser.add_argument(
        "--allow-project",
        help="Permit seeding into this exact project id (required for anything outside the dev project)",
    )
    args = parser.parse_args()

    base = args.base.rstrip("/")
    db = get_firestore_client()

    project = os.getenv("FB_PROJECT_ID")
    if project not in DEV_PROJECT_IDS and args.allow_project != project:
        print(
            f"\nRefusing to run: functions/.env points at project '{project}', which is not a known dev project "
            f"({', '.join(sorted(DEV_PROJECT_IDS))}).\n"
            "This script writes real partner_keys documents. If that is genuinely what you want, re-run with "
            f"--allow-project {project}",
            file=sys.stderr,
        )
        return 2

    print(f"\nSeeding smoke keys on project '{project}'")
    raw_key = seed_key(db, SMOKE_CONSUMER, FUNCTIONAL_RATE_LIMIT)
    throttle_key = seed_key(db, THROTTLE_CONSUMER, THROTTLE_RATE_LIMIT)
    revoked_key = seed_key(db, REVOKED_CONSUMER, 10, active=False)
    seeded = [raw_key, throttle_key, revoked_key]
    auth = {"X-API-Key": raw_key}

    try:
        return _run_checks(base, auth, throttle_key, revoked_key, args)
    finally:
        # finally, so an unwrapped HTTP error (emulator down, timeout) still
        # removes the key documents this run created.
        if args.keep_key:
            print(f"\nKept keys: {', '.join(seeded)}")
        else:
            cleanup(db, seeded)
            print("\nCleaned up seeded keys.")


def _run_checks(base: str, auth: dict, throttle_key: str, revoked_key: str, args) -> int:
    print(f"Target: {base}\n")
    print("AUTHENTICATION")

    check(
        "missing key is 401",
        lambda: _expect_error(requests.get(f"{base}/v1/schemes", timeout=60), 401, "missing_key"),
    )
    check(
        "unknown key is 401",
        lambda: _expect_error(
            requests.get(f"{base}/v1/schemes", headers={"X-API-Key": "nope"}, timeout=60), 401, "invalid_key"
        ),
    )
    check(
        "revoked key is 403",
        lambda: _expect_error(
            requests.get(f"{base}/v1/schemes", headers={"X-API-Key": revoked_key}, timeout=60), 403, "revoked_key"
        ),
    )

    print("\nROUTING AND VERSIONING")

    check(
        "missing version is 404 unsupported_version",
        lambda: _expect_error(requests.get(f"{base}/schemes", headers=auth, timeout=60), 404, "unsupported_version"),
    )
    check(
        "unknown version is 404 unsupported_version",
        lambda: _expect_error(requests.get(f"{base}/v2/schemes", headers=auth, timeout=60), 404, "unsupported_version"),
    )
    check(
        "unknown resource is 404 not_found",
        lambda: _expect_error(requests.get(f"{base}/v1/agencies", headers=auth, timeout=60), 404, "not_found"),
    )
    check(
        "POST on the collection is 405",
        lambda: _expect_error(requests.post(f"{base}/v1/schemes", headers=auth, timeout=60), 405, "method_not_allowed"),
    )
    check(
        "GET on /v1/schemes/search is 405, not a detail lookup",
        lambda: _expect_error(
            requests.get(f"{base}/v1/schemes/search", headers=auth, timeout=60), 405, "method_not_allowed"
        ),
    )
    check(
        "unsupported query param is 400",
        lambda: _expect_error(
            requests.get(f"{base}/v1/schemes?is_warmup=true", headers=auth, timeout=60), 400, "invalid_request"
        ),
    )

    print("\nLIST")

    listing = requests.get(f"{base}/v1/schemes?limit=5", headers=auth, timeout=120)
    check("GET /v1/schemes returns 200 with data", lambda: _expect_list(listing))
    check("list response carries X-RateLimit-Remaining", lambda: _expect_rate_header(listing))
    check("no internal fields in list payload", lambda: _expect_no_leaks(listing))
    check("list fields are exactly the allowlist", lambda: _expect_allowlist(listing))
    check("no retired or inactive schemes in list", lambda: _expect_listed_only(listing))

    check(
        "category filter returns 200",
        lambda: _expect_list(requests.get(f"{base}/v1/schemes?category=healthcare&limit=3", headers=auth, timeout=120)),
    )

    print("\nDETAIL")

    scheme_id = _first_scheme_id(listing)
    if scheme_id:
        detail = requests.get(f"{base}/v1/schemes/{scheme_id}", headers=auth, timeout=60)
        check(f"GET /v1/schemes/{scheme_id} returns 200", lambda: _expect_detail(detail, scheme_id))
        check("detail fields are exactly the allowlist", lambda: _expect_allowlist(detail))
        check("no internal fields in detail payload", lambda: _expect_no_leaks(detail))
    else:
        check("detail lookup", lambda: (_ for _ in ()).throw(AssertionError("no scheme id available from list")))

    check(
        "unknown scheme id is 404",
        lambda: _expect_error(
            requests.get(f"{base}/v1/schemes/definitely-not-a-real-id", headers=auth, timeout=60), 404, "not_found"
        ),
    )

    print("\nSEARCH")

    search = requests.post(
        f"{base}/v1/schemes/search", headers=auth, json={"query": "financial help for elderly", "limit": 5}, timeout=180
    )
    check("POST /v1/schemes/search returns 200 with data", lambda: _expect_list(search))
    check("no internal fields in search payload", lambda: _expect_no_leaks(search))
    check("search fields are exactly the allowlist", lambda: _expect_allowlist(search))
    check("no retired or inactive schemes in search", lambda: _expect_listed_only(search))
    check(
        "empty query is 400",
        lambda: _expect_error(
            requests.post(f"{base}/v1/schemes/search", headers=auth, json={"query": "  "}, timeout=60),
            400,
            "invalid_request",
        ),
    )
    check(
        "non-object JSON body is 400, not 500",
        lambda: _expect_error(
            requests.post(f"{base}/v1/schemes/search", headers=auth, json=["not", "an", "object"], timeout=60),
            400,
            "invalid_request",
        ),
    )

    print("\nRATE LIMITING (own key, so it cannot starve the checks above)")

    check(
        "rate limit eventually returns 429 with Retry-After",
        lambda: _expect_rate_limited(base, {"X-API-Key": throttle_key}),
    )

    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"\n{'=' * 62}\n  {passed}/{total} checks passed\n{'=' * 62}\n")

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w") as handle:
            json.dump(
                {
                    "base": base,
                    "project": os.getenv("FB_PROJECT_ID"),
                    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                    "passed": passed,
                    "total": total,
                    "checks": results,
                },
                handle,
                indent=2,
            )
        print(f"JSON report: {args.json_out}")

    return 0 if passed == total else 1


# --------------------------------------------------------------------------
# Assertions
# --------------------------------------------------------------------------


def _body(response) -> dict:
    try:
        return response.json()
    except ValueError:
        raise AssertionError(f"non-JSON response ({response.status_code}): {response.text[:200]}") from None


def _expect_error(response, status: int, code: str) -> str:
    body = _body(response)
    assert response.status_code == status, f"expected {status}, got {response.status_code}: {body}"
    actual = body.get("error", {}).get("code")
    assert actual == code, f"expected error code '{code}', got '{actual}'"
    return f"{status} {code}"


def _expect_list(response) -> str:
    body = _body(response)
    assert response.status_code == 200, f"expected 200, got {response.status_code}: {body}"
    data = body.get("data")
    assert isinstance(data, list), f"'data' is not a list: {type(data)}"
    assert data, "'data' is empty"
    return f"200, {len(data)} schemes, total_count={body.get('total_count')}, has_more={body.get('has_more')}"


def _expect_detail(response, scheme_id: str) -> str:
    body = _body(response)
    assert response.status_code == 200, f"expected 200, got {response.status_code}: {body}"
    data = body.get("data") or {}
    assert data.get("scheme_id") == scheme_id, f"scheme_id mismatch: {data.get('scheme_id')} != {scheme_id}"
    return f"200, scheme='{str(data.get('scheme'))[:48]}'"


def _records(response) -> list[dict]:
    data = _body(response).get("data")
    if isinstance(data, dict):
        return [data]
    return data or []


def _expect_no_leaks(response) -> str:
    for record in _records(response):
        for field in LEAKY_FIELDS:
            assert field not in record, f"leaked internal field '{field}'"
    return f"none of {', '.join(LEAKY_FIELDS)} present in {len(_records(response))} record(s)"


def _expect_allowlist(response) -> str:
    allowed = set(PUBLIC_FIELDS)
    for record in _records(response):
        extra = set(record) - allowed
        assert not extra, f"fields outside the allowlist: {sorted(extra)}"
    return f"exactly {len(allowed)} allowlisted fields"


def _expect_listed_only(response) -> str:
    for record in _records(response):
        status = record.get("status")
        assert status not in NON_SEARCHABLE_STATUSES, f"non-searchable status '{status}' returned"
    return f"no {'/'.join(sorted(NON_SEARCHABLE_STATUSES))} schemes present"


def _expect_rate_header(response) -> str:
    remaining = response.headers.get("X-RateLimit-Remaining")
    assert remaining is not None, "X-RateLimit-Remaining header absent"
    return f"X-RateLimit-Remaining={remaining}, X-RateLimit-Limit={response.headers.get('X-RateLimit-Limit')}"


def _expect_rate_limited(base: str, auth: dict) -> str:
    """Burn the throttle key's budget, then confirm the block and its Retry-After."""
    attempts = THROTTLE_RATE_LIMIT + 2
    for _ in range(attempts):
        response = requests.get(f"{base}/v1/schemes?limit=1", headers=auth, timeout=60)
        if response.status_code == 429:
            body = _body(response)
            assert body.get("error", {}).get("code") == "rate_limited", f"wrong code: {body}"
            retry_after = response.headers.get("Retry-After")
            assert retry_after is not None, "429 without Retry-After header"
            return f"429 rate_limited, Retry-After={retry_after}"
    raise AssertionError(f"never rate limited after {attempts} requests over a {THROTTLE_RATE_LIMIT}/min budget")


def _first_scheme_id(response) -> str | None:
    try:
        data = _body(response).get("data") or []
        return data[0].get("scheme_id") if data else None
    except AssertionError:
        return None


if __name__ == "__main__":
    sys.exit(main())
