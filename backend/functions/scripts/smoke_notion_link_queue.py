"""
End-to-end smoke test for the Notion Link Queue sync against dev Firestore and a QA Notion copy.

Seeds three temporary ``schemes/zz-notion-qa-*`` documents in the dev project, runs the real
sync and metrics code against the real Notion API, prints a pass/fail table, then deletes the
documents it made. Notion rows are left in the QA copy (they resolve once the docs are gone).

Notion is prod-only (issue #443), so this never uses NOTION_* from ``.env``. The token and
data-source IDs come from ``functions/.env.notion-qa``, and the token must belong to a
connection that is shared with the QA copy only, so a bug here cannot reach the prod root:

    NOTION_API_TOKEN=...
    NOTION_LINK_QUEUE_DATA_SOURCE_ID=...
    NOTION_METRICS_DATA_SOURCE_ID=...

Refuses to run unless FB_PROJECT_ID is schemessg-v3-dev, because it writes `schemes` documents.

Usage — run as a module, so `functions/` is on the import path:
    cd backend/functions
    uv run python -m scripts.smoke_notion_link_queue | tee ../../notion-smoke-run.txt
"""

import os
import sys
from datetime import date, timedelta
from typing import Callable, List, Tuple

from batch_jobs import notion_link_queue as nlq
from dotenv import dotenv_values
from fb_manager.firebaseManager import get_firestore_client


DEV_PROJECT_ID = "schemessg-v3-dev"
QA_PREFIX = "zz-notion-qa-"


class CountingNotion(nlq.NotionClient):
    """Real Notion client that counts writes, to prove a rerun is a no-op."""

    def __init__(self, token: str):
        super().__init__(token)
        self.writes = 0

    def _call(self, method, path, body=None):
        if not path.endswith("/query"):
            self.writes += 1
        return super()._call(method, path, body)


def _failing(name: str, **extra) -> dict:
    return {
        "scheme": f"QA {name} (synthetic, safe to ignore)",
        "agency": "SchemesSG QA",
        "link": f"https://example.org/schemessg-qa/{name}",
        "status": "inactive",
        "status_reason": "Dead link (hard_dead, 3 consecutive checks)",
        "link_check_status_code": 404,
        "link_check_error": "Not Found",
        "link_check_fail_streak": 3,
        "link_check_fail_class": "hard_dead",
        "last_link_check": "2026-10-05T09:01:00+00:00",
        **extra,
    }


def load_qa_config() -> dict:
    """QA Notion config from functions/.env.notion-qa; exits unless this is the dev project."""
    if os.getenv("FB_PROJECT_ID") != DEV_PROJECT_ID:
        sys.exit(f"Refusing: FB_PROJECT_ID is {os.getenv('FB_PROJECT_ID')!r}, expected {DEV_PROJECT_ID!r}")
    qa = dotenv_values(".env.notion-qa")
    cfg = {
        "token": qa.get("NOTION_API_TOKEN") or "",
        "link_queue": qa.get("NOTION_LINK_QUEUE_DATA_SOURCE_ID") or "",
        "metrics": qa.get("NOTION_METRICS_DATA_SOURCE_ID") or "",
    }
    if not all(cfg.values()):
        sys.exit("Refusing: functions/.env.notion-qa must set NOTION_API_TOKEN and both data-source IDs")
    return cfg


def main() -> int:
    cfg = load_qa_config()

    db = get_firestore_client()
    schemes = db.collection("schemes")
    notion = CountingNotion(cfg["token"])
    results: List[Tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    def sync() -> dict:
        return nlq.run_notion_link_queue_sync_core(db, cfg=cfg, notion=notion)

    def rows() -> dict:
        return {
            row.get("Scheme ID"): row
            for row in (nlq._decode_row(page) for page in notion.query_all(cfg["link_queue"]))
        }

    def step(name: str, action: Callable[[], None]) -> None:
        try:
            action()
        except Exception as exc:  # report and keep going so cleanup still runs
            check(name, False, f"raised {exc!r}")

    seeded = {
        f"{QA_PREFIX}1": _failing("1"),
        f"{QA_PREFIX}2": _failing(
            "2",
            status=None,
            link_suspect=True,
            link_check_status_code=503,
            link_check_error="Service Unavailable",
            link_check_fail_class="transient",
            link_check_fail_streak=1,
            status_reason=None,
        ),
        f"{QA_PREFIX}3": _failing(
            "3",
            link_check_status_code=502,
            link_check_error="Bad Gateway",
            link_check_fail_class="transient",
            link_check_fail_streak=18,
            status_reason="Dead link detected",
        ),
    }
    try:
        for doc_id, data in seeded.items():
            schemes.document(doc_id).set({k: v for k, v in data.items() if v is not None})

        def first_sync():
            result = sync()
            queue = {d.id for d in schemes.stream() if nlq.in_queue(d.to_dict() or {})}
            current = rows()
            check("1 sync creates a row per queued scheme", queue <= set(current), f"queue {len(queue)}, {result}")
            row = current.get(f"{QA_PREFIX}1", {})
            facts = nlq.scheme_facts(f"{QA_PREFIX}1", seeded[f"{QA_PREFIX}1"])
            check(
                "1 facts round-trip through Notion",
                all(row.get(k) == v for k, v in facts.items()),
                str({k: (row.get(k), v) for k, v in facts.items() if row.get(k) != v}),
            )
            check(
                "1 missing status shows as active",
                current.get(f"{QA_PREFIX}2", {}).get("Firestore status") == "active",
            )

        def rerun_is_noop():
            notion.writes = 0
            sync()
            check("2 second sync writes nothing", notion.writes == 0, f"{notion.writes} writes")

        def recover_and_fail_again():
            schemes.document(f"{QA_PREFIX}1").set(
                {"scheme": "QA 1 (synthetic, safe to ignore)", "link": "https://example.org"}
            )
            sync()
            row = rows()[f"{QA_PREFIX}1"]
            check(
                "3 recovered scheme resolves",
                (row["Sync state"], row["Sync message"]) == ("Resolved", "Link is working again"),
            )
            schemes.document(f"{QA_PREFIX}1").set(_failing("1"))
            sync()
            row = rows()[f"{QA_PREFIX}1"]
            check(
                "4 failing again reopens",
                (row["Sync state"], row["Sync message"]) == ("Open", "Failing the link check again"),
            )

        def retire_and_delete():
            schemes.document(f"{QA_PREFIX}3").update({"status": "retired"})
            schemes.document(f"{QA_PREFIX}2").delete()
            sync()
            current = rows()
            check("5 retired scheme resolves", current[f"{QA_PREFIX}3"]["Sync message"] == "Scheme retired")
            check("6 deleted scheme resolves", current[f"{QA_PREFIX}2"]["Sync message"] == "Scheme no longer exists")

        def metrics():
            today = date.today()
            first = nlq.append_metrics_row(db, 1, 2, cfg=cfg, notion=notion, today=today)
            again = nlq.append_metrics_row(db, 1, 2, cfg=cfg, notion=notion, today=today)
            pages = {p["id"]: nlq._decode_row(p) for p in notion.query_all(cfg["metrics"])}
            week = nlq._iso_week(today)
            check(
                "7 metrics upsert by week", first == again and sum(r.get("Week") == week for r in pages.values()) == 1
            )
            total = sum(1 for _ in schemes.stream())
            check(
                "7 metrics totals match Firestore",
                pages[first]["Total schemes"] == total,
                f"{pages[first]} vs {total}",
            )
            nxt = nlq.append_metrics_row(db, 0, 0, cfg=cfg, notion=notion, today=today + timedelta(days=7))
            pages = {p["id"]: nlq._decode_row(p) for p in notion.query_all(cfg["metrics"])}
            check("8 Latest moves to the newest row", [pid for pid, r in pages.items() if r.get("Latest")] == [nxt])
            nlq.append_metrics_row(db, 1, 2, cfg=cfg, notion=notion, today=today)  # leave QA on this week

        step("1 first sync", first_sync)
        step("2 rerun", rerun_is_noop)
        step("3-4 recover/fail", recover_and_fail_again)
        step("5-6 retire/delete", retire_and_delete)
        step("7-8 metrics", metrics)
    finally:
        for doc_id in seeded:
            schemes.document(doc_id).delete()
        sync()  # QA rows for the deleted docs resolve

    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
