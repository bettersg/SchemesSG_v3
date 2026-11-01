"""Read-only Firestore lookup for operators: print documents as JSON lines, never write.

Usage (from backend/functions):
    uv run python scripts/firestore_peek.py dev schemes IjOCYQTyaoaNiIJCNyjC v2PvcSMRLJv39bQn6OxS --fields scheme,phone
    uv run python scripts/firestore_peek.py prod schemeEntries --where pipeline_status=failed --fields Scheme,Link
    uv run python scripts/firestore_peek.py prod schemeEntries --since 2026-11-01T12:30:00Z --fields Scheme,pipeline_status,llm_fields
    uv run python scripts/firestore_peek.py prod schemes --where link=https://www.wings.sg/icope/ --count

--fields reads only those fields (Firestore select), so a collection scan stays cheap. Without --fields every field
except the bulky ones (scraped_text, embedding) is printed. Long strings are cut to --max-chars.
--where is equality on one field (repeatable; a value that parses as JSON is used as JSON, e.g. true, 3, null).
--since keeps documents created at or after an ISO 8601 time (filtered here, on document create_time).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


sys.path.insert(0, str(Path(__file__).resolve().parent))
from firestore_env import ENVIRONMENTS, firestore_client, load_environment  # noqa: E402
from google.cloud.firestore_v1.base_query import FieldFilter  # noqa: E402


BULKY_FIELDS = ("scraped_text", "embedding")


def parse_args(argv: Optional[Sequence[str]] = None):
    p = argparse.ArgumentParser(description="Read-only Firestore lookup (JSON lines).")
    p.add_argument("env", choices=ENVIRONMENTS)
    p.add_argument("collection")
    p.add_argument("doc_ids", nargs="*", help="read these documents instead of querying")
    p.add_argument("--where", action="append", default=[], metavar="FIELD=VALUE")
    p.add_argument("--since", help="ISO 8601; documents created at or after it")
    p.add_argument("--fields", help="comma-separated fields to read")
    p.add_argument("--limit", type=int, default=50, help="max documents printed (default 50)")
    p.add_argument("--max-chars", type=int, default=300, help="cut longer strings (0 = no cut)")
    p.add_argument("--count", action="store_true", help="print only the number of matching documents")
    return p.parse_args(argv)


def parse_where(raw: str):
    field, sep, value = raw.partition("=")
    if not sep or not field:
        sys.exit(f"--where needs FIELD=VALUE, got {raw!r}")
    try:
        return field, json.loads(value)
    except json.JSONDecodeError:
        return field, value


def parse_since(raw: str) -> datetime:
    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def shorten(value: Any, max_chars: int) -> Any:
    if isinstance(value, str) and max_chars and len(value) > max_chars:
        return value[:max_chars] + f"… (+{len(value) - max_chars} chars)"
    if isinstance(value, list):
        return [shorten(v, max_chars) for v in value]
    if isinstance(value, dict):
        return {k: shorten(v, max_chars) for k, v in value.items()}
    return value


def get_path(data: Dict[str, Any], path: str) -> Any:
    """Value at a dotted field path such as llm_fields.scheme_type (None when any part is missing)."""
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def render(snap, fields: Optional[List[str]], max_chars: int) -> Dict[str, Any]:
    data = snap.to_dict() or {}
    if fields is None:
        data = {k: v for k, v in data.items() if k not in BULKY_FIELDS}
    else:
        data = {f: get_path(data, f) for f in fields}
    return {"_id": snap.id, "_created": snap.create_time.isoformat(), **shorten(data, max_chars)}


def snapshots(db, args, fields: Optional[List[str]]):
    collection = db.collection(args.collection)
    if args.doc_ids:
        for doc_id in args.doc_ids:
            snap = collection.document(doc_id).get(field_paths=fields)
            if snap.exists:
                yield snap
            else:
                print(json.dumps({"_id": doc_id, "_missing": True}))
        return
    query = collection
    for field, value in map(parse_where, args.where):
        query = query.where(filter=FieldFilter(field, "==", value))
    if fields is not None:
        query = query.select(fields)
    since = parse_since(args.since) if args.since else None
    for snap in query.stream():
        if since is None or snap.create_time >= since:
            yield snap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    fields = [f.strip() for f in args.fields.split(",") if f.strip()] if args.fields else None
    load_environment(args.env)
    db = firestore_client("firestore_peek")
    printed = 0
    for snap in snapshots(db, args, fields):
        printed += 1
        if not args.count and printed <= args.limit:
            print(json.dumps(render(snap, fields, args.max_chars), default=str, ensure_ascii=False))
    if args.count:
        print(printed)
    elif printed > args.limit:
        print(f"# {printed} matched, printed {args.limit} (raise --limit)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
