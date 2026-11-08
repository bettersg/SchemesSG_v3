"""
Dry run of the monthly content check (issue #407).

Same scrape, page-hash compare and AI review as the monthly content check, but nothing is written to
Firestore: the stored hashes stay as the baseline, so the run can be repeated to count how many
schemes get flagged.

- First run: picks --limit schemes that already have hashes (in ID order) and saves their IDs to
  sample.json in the output folder.
- Later runs: --sample <file> checks the same schemes again, so runs can be compared.
- Each run writes run_<date>_<time>.json: outcome counts, plus per scheme the changed pages and
  the AI's suggestions (old value, new value, quote, page URL).

Development Firestore only (stops unless FB_PROJECT_ID is schemessg-v3-dev). Run it in the
scheme-processor image, from backend/scheme-processor (create the output folder first so its
files belong to you):

    mkdir -p data/content-check-dry-run
    docker run --rm -v "$PWD/app:/src/app" -v "$PWD/scripts:/src/scripts" \\
      -v "$PWD/data:/src/data" -v "<path to .env.dev>:/src/.env.dev:ro" -w /src \\
      --entrypoint /app/.venv/bin/python schemessg-dev-smoke-scheme-processor \\
      -m scripts.dry_run_content_check --env .env.dev --limit 50
"""

import argparse
import asyncio
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


DEV_PROJECT = "schemessg-v3-dev"


def pick_sample(db, limit: int):
    """The first `limit` schemes (by ID) that already have stored page hashes."""
    ids = []
    for doc in db.collection("schemes").select(["content_pages"]).stream():
        if isinstance((doc.to_dict() or {}).get("content_pages"), list):
            ids.append(doc.id)
            if len(ids) == limit:
                break
    return ids


async def run(db, scheme_ids):
    from app.content_check import ContentStore, changed_pages, check_scheme, scraped_pages, stored_pages
    from app.services.scraper import scrape_url

    class DryRunStore(ContentStore):
        """Real reads; every write is only noted down."""

        def __init__(self, db):
            super().__init__(db)
            self.scheme = None
            self.flagged = None

        def get_scheme(self, scheme_id):
            self.scheme = super().get_scheme(scheme_id)
            return self.scheme

        def record_failure(self, scheme_id):
            pass

        def save_pages(self, scheme_id, pages, now):
            pass

        def save_flagged(self, scheme_id, record, now):
            self.flagged = record
            return "dry-run"

    results = []
    for n, scheme_id in enumerate(scheme_ids, 1):
        store = DryRunStore(db)
        scraped = {}

        async def scrape(url):
            scraped.update(await scrape_url(url, content_check=True))
            return scraped

        try:
            res = await check_scheme(scheme_id, store, scrape)
        except Exception as e:
            res = {"scheme_id": scheme_id, "outcome": "error", "detail": f"{type(e).__name__}: {e}"[:500]}

        scheme = store.scheme or {}
        old = stored_pages(scheme)
        new = scraped_pages(scraped) if scraped else {}
        record = store.flagged or {}
        results.append(
            {
                "scheme_id": scheme_id,
                "scheme": scheme.get("scheme"),
                "link": scheme.get("link"),
                "outcome": res["outcome"],
                "detail": res.get("detail"),
                "pages_changed": changed_pages(old, new) if old is not None and new else [],
                "suggestions": [
                    {
                        "field": s.get("field"),
                        "old_value": scheme.get(s.get("field")),
                        "new_value": s.get("new_value"),
                        "quote": s.get("quote"),
                        "page_url": s.get("page_url"),
                    }
                    for s in record.get("suggestions") or []
                ],
                "contacts_gone": record.get("contact_check") or [],
            }
        )
        print(f"[{n}/{len(scheme_ids)}] {scheme_id} {res['outcome']} {res.get('detail') or ''}", flush=True)
    return results


def summary(results):
    return {
        "schemes": len(results),
        "outcomes": dict(Counter(r["outcome"] for r in results)),
        "schemes_with_changed_pages": sum(1 for r in results if r["pages_changed"]),
        "suggestions": sum(len(r["suggestions"]) for r in results),
        "suggestions_by_field": dict(Counter(s["field"] for r in results for s in r["suggestions"]).most_common()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--env", help="env file with development FB_* and AZURE_OPENAI_*_SEA settings")
    parser.add_argument("--limit", type=int, default=50, help="schemes to pick when no --sample is given")
    parser.add_argument("--sample", help="sample.json from an earlier run, to check the same schemes")
    parser.add_argument("--out", default="data/content-check-dry-run", help="output folder")
    args = parser.parse_args()

    if args.env:
        load_dotenv(args.env, override=True)
    if os.getenv("FB_PROJECT_ID") != DEV_PROJECT:
        raise SystemExit(f"FB_PROJECT_ID must be {DEV_PROJECT}; dry runs never use production")

    from app.clients.firestore import get_firestore_client

    db = get_firestore_client()
    if db is None:
        raise SystemExit("Firestore not configured")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.sample:
        scheme_ids = json.loads(Path(args.sample).read_text())
    else:
        scheme_ids = pick_sample(db, args.limit)
        (out / "sample.json").write_text(json.dumps(scheme_ids, indent=2))
        print(f"Picked {len(scheme_ids)} schemes; saved to {out / 'sample.json'}")

    started = datetime.now()
    results = asyncio.run(run(db, scheme_ids))
    report = {
        "started": started.isoformat(timespec="seconds"),
        "finished": datetime.now().isoformat(timespec="seconds"),
        "summary": summary(results),
        "results": results,
    }
    path = out / f"run_{started:%Y-%m-%d_%H%M}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    # Docker runs as root (Playwright's browsers live in root's home): give the files to whoever owns the folder.
    owner = out.stat()
    for written in (path, out / "sample.json"):
        if written.exists() and os.geteuid() == 0:
            os.chown(written, owner.st_uid, owner.st_gid)
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
