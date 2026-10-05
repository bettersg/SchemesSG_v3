"""
Dev end-to-end check for Notion Link Queue verdict write-back (#443), in two phases around a
human step in dev Slack.

    cd backend/functions
    uv run python -m scripts.smoke_notion_link_queue_verdicts start
    # In dev Slack: approve the "Scheme Update" card for "QA v-moved", and reject the
    # retirement card for "QA v-retire" with a reason.
    uv run python -m scripts.smoke_notion_link_queue_verdicts finish

``start`` seeds ``schemes/zz-notion-v-*`` in the dev project, sets a verdict on each QA row
through the Notion API (as a volunteer would), runs the real sync, and checks each outcome.
The dev ``on_new_scheme_entry`` trigger and scheme-processor then post the normal Slack cards.
``finish`` syncs again, checks the maintainer outcomes, resubmits the rejected Retire, then
deletes the schemes and schemeEntries it made. Same guards as ``smoke_notion_link_queue``.
"""

import sys
import time
from typing import List, Tuple

from batch_jobs import notion_link_queue as nlq
from fb_manager.firebaseManager import get_firestore_client
from scripts.smoke_notion_link_queue import CountingNotion, _failing, load_qa_config


PREFIX = "zz-notion-v-"
REVIEWER_EMAIL = "tracilim@better.sg"
NEW_URL = "https://www.supportgowhere.gov.sg/"  # a real page, so scheme-processor can scrape it
HUMAN_TYPES = {
    "Verdict": "select",
    "New URL": "url",
    "Retire reason": "rich_text",
    "Note": "rich_text",
    "Verdict by": "people",
}
SEED = {name: _failing(f"v-{name}") for name in ("moved", "retire", "checker", "unclear", "bad")}


def main(phase: str) -> int:
    cfg = load_qa_config()
    db = get_firestore_client()
    notion = CountingNotion(cfg["token"])
    results: List[Tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    def sync() -> dict:
        return nlq.run_notion_link_queue_sync_core(db, cfg=cfg, notion=notion)

    def pages() -> dict:
        return {nlq._decode_row(p).get("Scheme ID"): p for p in notion.query_all(cfg["link_queue"])}

    def row(name: str) -> dict:
        return nlq._decode_row(pages()[PREFIX + name])

    def entry(entry_id: str) -> dict:
        return db.collection("schemeEntries").document(entry_id).get().to_dict() or {}

    def set_verdict(name: str, **values) -> None:
        notion.update_page(pages()[PREFIX + name]["id"], nlq.encode_properties(values, HUMAN_TYPES))

    if phase == "start":
        users = notion._call("GET", "/users")["results"]
        reviewer = next(u["id"] for u in users if (u.get("person") or {}).get("email") == REVIEWER_EMAIL)
        by = [{"id": reviewer}]
        for name, data in SEED.items():
            db.collection("schemes").document(PREFIX + name).set(data)
        sync()
        set_verdict("moved", **{"Verdict": "Moved", "New URL": NEW_URL, "Note": "QA: moved", "Verdict by": by})
        set_verdict("retire", **{"Verdict": "Retire", "Retire reason": "QA: programme ended", "Verdict by": by})
        set_verdict("checker", **{"Verdict": "Checker wrong", "Verdict by": by})
        set_verdict("unclear", **{"Verdict": "Unclear", "Note": "QA: unsure", "Verdict by": by})
        set_verdict("bad", **{"Verdict": "Moved", "New URL": SEED["bad"]["link"], "Verdict by": by})
        sync()

        moved, retire = row("moved"), row("retire")
        moved_entry, retire_entry = entry(moved["Entry ID"]), entry(retire["Entry ID"])
        check(
            "Moved -> Submitted with entry -1", moved["Sync state"] == "Submitted" and moved["Entry ID"].endswith("-1")
        )
        check(
            "Moved entry has the update_scheme shape",
            moved_entry.get("typeOfRequest") == "update"
            and moved_entry.get("targetSchemeId") == PREFIX + "moved"
            and (moved_entry.get("Link"), moved_entry.get("oldLink")) == (NEW_URL, SEED["moved"]["link"])
            and moved_entry.get("userEmail") == REVIEWER_EMAIL,
            str({k: moved_entry.get(k) for k in ("typeOfRequest", "Link", "oldLink", "userEmail", "pipeline_status")}),
        )
        check(
            "Retire -> Submitted, retire entry",
            retire["Sync state"] == "Submitted" and retire_entry.get("typeOfRequest") == "retire",
        )
        checker = db.collection("schemes").document(PREFIX + "checker").get().to_dict()
        check(
            "Checker wrong -> Applied, scheme restored and verified",
            row("checker")["Sync state"] == "Applied"
            and checker.get("status") == "active"
            and checker.get("link_check_manual_verified_by") == REVIEWER_EMAIL
            and not set(nlq.CHECKER_WRONG_CLEARS) & set(checker),
            str({k: checker.get(k) for k in ("status", "status_reason", "link_check_manual_verified_by")}),
        )
        check("Unclear -> Parked", row("unclear")["Sync state"] == "Parked")
        bad = row("bad")
        check(
            "Same-URL Moved -> Rejected with a plain message",
            (bad["Sync state"], bad["Sync message"]) == ("Rejected", "New URL is the same as the current link."),
        )
        notion.writes = 0
        sync()
        check("Rerun writes nothing", notion.writes == 0, f"{notion.writes} writes")

        deadline = time.time() + 300
        while time.time() < deadline and not (
            entry(moved["Entry ID"]).get("slack_message_ts") and entry(retire["Entry ID"]).get("slack_message_ts")
        ):
            time.sleep(15)
        for label, entry_id in (("update", moved["Entry ID"]), ("retirement", retire["Entry ID"])):
            posted = entry(entry_id)
            check(
                f"Slack {label} card posted",
                bool(posted.get("slack_message_ts")),
                f"pipeline_status={posted.get('pipeline_status')}",
            )
        print("\nNext: in dev Slack, APPROVE the update card for 'QA v-moved' and REJECT (with a reason)")
        print("the retirement card for 'QA v-retire'. Then run: ... smoke_notion_link_queue_verdicts finish\n")

    elif phase == "finish":
        sync()
        moved = row("moved")
        scheme = db.collection("schemes").document(PREFIX + "moved").get().to_dict()
        check(
            "Approved Moved -> Resolved",
            (moved["Sync state"], moved["Sync message"]) == ("Resolved", "Approved by a maintainer"),
            moved["Sync message"],
        )
        check(
            "Approval cleared the scheme's link-check state (#450)",
            scheme.get("status") == "active"
            and not {"link_check_fail_streak", "link_suspect", "link_check_error"} & set(scheme),
            str({k: scheme.get(k) for k in ("status", "link", "link_check_fail_streak", "link_suspect")}),
        )
        retire = row("retire")
        check(
            "Rejected Retire -> Open, Verdict cleared, reason shown",
            retire["Sync state"] == "Open"
            and retire["Verdict"] is None
            and retire["Sync message"].startswith("A maintainer rejected this"),
            retire["Sync message"],
        )
        set_verdict("retire", Verdict="Retire")
        sync()
        retire = row("retire")
        check(
            "Resubmitted Retire uses entry -2",
            retire["Sync state"] == "Submitted" and retire["Entry ID"].endswith("-2"),
            retire["Entry ID"],
        )
        notion.writes = 0
        sync()
        check("No resubmit loop", notion.writes == 0, f"{notion.writes} writes")

        made = [
            d.id
            for d in db.collection("schemeEntries").stream()
            if str((d.to_dict() or {}).get("targetSchemeId", "")).startswith(PREFIX)
        ]
        for entry_id in made:
            db.collection("schemeEntries").document(entry_id).delete()
        for name in SEED:
            db.collection("schemes").document(PREFIX + name).delete()
        sync()
        print(f"Cleaned up {len(SEED)} schemes and {len(made)} schemeEntries in dev.")
    else:
        sys.exit("phase must be 'start' or 'finish'")

    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
