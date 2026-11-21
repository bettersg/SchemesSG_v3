"""Apply reviewed field corrections to `schemes` documents: dry run, field backup, guarded write, restore.

Usage (from backend/functions):
    uv run python scripts/patch_schemes.py dev PATCH.json                     # dry run: per-field old -> new
    uv run python scripts/patch_schemes.py dev PATCH.json --write             # rehearse on dev
    uv run python scripts/patch_schemes.py prod PATCH.json                    # dry run on prod
    uv run python scripts/patch_schemes.py prod PATCH.json --write --confirm-project schemessg
    uv run python scripts/patch_schemes.py prod --restore BACKUP.json --write --confirm-project schemessg

PATCH.json maps a scheme id to the fields to set, an optional label and an optional guard:
    {
      "v2PvcSMRLJv39bQn6OxS": {
        "label": "Home Caregiving Grant",
        "expect": {"llm_description": "$400"},
        "set": {"summary": "Monthly cash grant of $200 to $600 for caregivers of persons with disabilities."}
      }
    }

- `expect`: each field must currently contain that substring (or equal it, for non-strings). A scheme that fails
  its guard was already fixed or edited differently; it is reported and skipped.
- who_is_it_for / what_it_gives / scheme_type values must be current taxonomy terms (new_scheme.taxonomy).
- --write first saves the old values of every touched field to --backup-dir (default: the repo's gitignored data/
  folder), then writes each scheme with a last_update_time precondition, so a scheme edited since the read is
  skipped, not overwritten. Each write stamps last_scraped_update, as an approved edit does, so the partner API's
  updated_at / updated_since report the change.
- Afterwards: re-embed (scripts/populate_embeddings.py) when text or tags changed, and see docs/data-changes.md
  for the prerendered-page refresh.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


sys.path.insert(0, str(Path(__file__).resolve().parent))
from firestore_env import (  # noqa: E402  (puts backend/functions on sys.path)
    ENVIRONMENTS,
    firestore_client,
    load_environment,
)
from google.cloud.firestore import SERVER_TIMESTAMP  # noqa: E402
from new_scheme import taxonomy  # noqa: E402


DEFAULT_BACKUP_DIR = Path(__file__).resolve().parents[3] / "data" / "patches"
STAMP_FIELD = "last_scraped_update"


def parse_args(argv: Optional[Sequence[str]] = None):
    p = argparse.ArgumentParser(description="Apply reviewed field corrections to schemes documents.")
    p.add_argument("env", choices=ENVIRONMENTS)
    p.add_argument("patch", nargs="?", help="PATCH.json")
    p.add_argument("--restore", metavar="BACKUP", help="write a backup file's old values back")
    p.add_argument("--write", action="store_true", help="write; without it this is a dry run")
    p.add_argument("--confirm-project", help="required with prod --write: schemessg")
    p.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    args = p.parse_args(argv)
    if bool(args.patch) == bool(args.restore):
        p.error("give a PATCH.json or --restore BACKUP, not both")
    if args.write and args.env == "prod" and args.confirm_project != ENVIRONMENTS["prod"][1]:
        p.error("prod --write needs --confirm-project schemessg")
    return args


def load_patch(path: str) -> Dict[str, Dict[str, Any]]:
    """Read PATCH.json and exit on a malformed entry or an off-vocabulary tag."""
    patch = json.loads(Path(path).read_text())
    problems = []
    for doc_id, entry in patch.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("set"), dict) or not entry["set"]:
            problems.append(f"{doc_id}: needs a non-empty 'set' object")
            continue
        for field in taxonomy.FIELDS:
            if field in entry["set"]:
                values = entry["set"][field]
                if not isinstance(values, list):
                    problems.append(f"{doc_id}: {field} must be a list")
                    continue
                unknown = [v for v in values if v not in taxonomy.term_names(field)]
                if unknown:
                    problems.append(f"{doc_id}: {field} has off-vocabulary terms {unknown}")
    if problems:
        sys.exit("bad patch:\n  " + "\n  ".join(problems))
    return patch


def guard_failures(current: Dict[str, Any], expect: Dict[str, Any]) -> List[str]:
    failures = []
    for field, wanted in expect.items():
        value = current.get(field)
        ok = wanted in value if isinstance(wanted, str) and isinstance(value, str) else value == wanted
        if not ok:
            failures.append(f"{field} lacks {wanted!r}")
    return failures


def plan(db, patch: Dict[str, Dict[str, Any]]) -> List[Tuple[Any, str, Dict[str, Any]]]:
    """Read every scheme, print its diff, and return (snapshot, label, changed fields) for those to write."""
    planned = []
    for doc_id, entry in patch.items():
        label = entry.get("label") or doc_id
        snap = db.collection("schemes").document(doc_id).get()
        if not snap.exists:
            print(f"SKIP {doc_id} {label}: not found")
            continue
        current = snap.to_dict()
        failures = guard_failures(current, entry.get("expect", {}))
        if failures:
            print(f"SKIP {doc_id} {label}: guard failed ({'; '.join(failures)}). Already fixed or edited?")
            continue
        diff = {f: v for f, v in entry["set"].items() if current.get(f) != v}
        print(f"\n== {doc_id} {label}: {len(diff)} field(s) change")
        for field, value in diff.items():
            print(f"  {field}:\n    old: {json.dumps(current.get(field), ensure_ascii=False, default=str)}")
            print(f"    new: {json.dumps(value, ensure_ascii=False)}")
        if diff:
            planned.append((snap, label, diff))
    return planned


def write(db, env: str, planned, backup_dir: Path) -> int:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"backup-schemes-{env}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    old = {snap.id: {f: snap.to_dict().get(f) for f in [*diff, STAMP_FIELD]} for snap, _, diff in planned}
    backup.write_text(json.dumps(old, default=str, ensure_ascii=False, indent=2))
    print(f"\nbackup -> {backup}")
    written = 0
    for snap, label, diff in planned:
        try:
            snap.reference.update(
                {**diff, STAMP_FIELD: SERVER_TIMESTAMP}, option=db.write_option(last_update_time=snap.update_time)
            )
        except Exception as e:  # FailedPrecondition when the scheme changed after the read
            print(f"SKIP {snap.id} {label}: {e}")
            continue
        written += 1
        print(f"wrote {snap.id} {label}")
    print(f"wrote {written} of {len(planned)} schemes to {env}")
    return written


def restore(db, env: str, path: str, write_it: bool) -> None:
    """Put a backup's field values back. The stamp is set to now, not restored, so partners resync the scheme."""
    backup = json.loads(Path(path).read_text())
    for doc_id, fields in backup.items():
        fields = {f: v for f, v in fields.items() if f != STAMP_FIELD}
        if not write_it:
            print(f"would restore {doc_id}: {sorted(fields)}")
            continue
        db.collection("schemes").document(doc_id).update({**fields, STAMP_FIELD: SERVER_TIMESTAMP})
        print(f"restored {doc_id}: {sorted(fields)}")
    if not write_it:
        print(f"dry run on {env} (add --write)")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    patch = load_patch(args.patch) if args.patch else None
    load_environment(args.env)
    db = firestore_client("patch_schemes")
    if args.restore:
        restore(db, args.env, args.restore, args.write)
        return 0
    planned = plan(db, patch)
    if not args.write:
        print(f"\ndry run on {args.env}: {len(planned)} scheme(s) would change (add --write)")
        return 0
    write(db, args.env, planned, args.backup_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
