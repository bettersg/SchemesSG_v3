"""Reclassify every scheme with the production tagger: snapshot -> classify (frozen results) -> report/xlsx -> apply.

Writes only who_is_it_for / what_it_gives / scheme_type. Parents and the 10 categories are derived from those at read time.
All files live under data/reclass/ (gitignored: they hold scheme data).

usage (from backend/scripts/ncss_eval):
  reclassify.py snapshot prod|dev           READ-ONLY copy of every scheme -> snapshot-<env>.jsonl
  reclassify.py classify [--ids FILE] [--force]
                                            tag schemes lacking a result for the current input text + prompt (resumable).
                                            --ids = targeted re-run for NCSS feedback; --force ignores existing results
  reclassify.py report                      per-term old/new counts, changed schemes -> report.md
  reclassify.py xlsx                        NCSS/partner review workbook -> ncss_review.xlsx
  reclassify.py apply dev|prod [--write] [--confirm-project ID]
                                            dry-run by default; --write backs up the live tags, then updates the 3 fields
                                            and stamps tags_updated_at (partner updated_since sees the re-tag).
                                            prod --write also needs --confirm-project schemessg; take a fresh prod snapshot first.
  reclassify.py restore dev|prod BACKUP [--write] [--confirm-project ID]
                                            rollback: writes a backup-<env>-*.jsonl back (same prod guard)
"""
import argparse
import hashlib
import json
import os
import sys
import time
import types
from collections import Counter
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scheme-processor"))
sys.modules.setdefault("loguru", types.SimpleNamespace(logger=types.SimpleNamespace(error=print, warning=print, info=print)))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parent.parent / "scheme-processor/.env")  # AZURE_OPENAI_* with the gpt-6-luna deployment
from app import taxonomy as tx  # noqa: E402
from app.services import taxonomy_tagger as tagger  # noqa: E402

import logging  # noqa: E402

logging.getLogger("app.taxonomy").setLevel(logging.ERROR)  # prod holds many off-vocabulary legacy tags; the report counts them

OUT = HERE / "data" / "reclass"
FIELDS = tx.FIELDS
SNAPSHOT_KEYS = ["scheme", "agency", "link", "description", "llm_description", "summary", "eligibility", "status",
                 "who_is_it_for", "what_it_gives", "scheme_type"]
ENVS = {"prod": ("../../functions/.env.prod", "schemessg"), "dev": ("../../functions/.env.dev", "schemessg-v3-dev")}


# ------------------------------------------------------------------ pure logic (unit-tested)
def input_hash(fields):
    """Hash of exactly what the model sees plus the prompt: a stored result is reusable only if both are unchanged."""
    text = tagger.build_user_text(fields) + "\x00" + tagger.build_system_prompt() + "\x00" + tagger.TAGGING_EFFORT
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def needs_classification(scheme, existing, force=False):
    return force or existing is None or existing.get("input_hash") != input_hash(scheme)


def new_tags(raw_json):
    """Model JSON -> validated v2 tags (vocabulary check + code-derived age bands) plus the raw model fields kept for review."""
    data = json.loads(raw_json)
    tags = tagger.parse_tagging_response(raw_json)
    return {**tags, "age_min": data.get("age_min"), "age_max": data.get("age_max"), "rationale": data.get("rationale", "")}


def old_in_new_vocabulary(scheme):
    """The scheme's current tags translated to the v2 vocabulary (what the code would show for un-migrated data)."""
    translated = tx.translate_legacy({f: scheme.get(f) for f in FIELDS})
    return {f: translated[f] for f in FIELDS}


def changed_fields(scheme, result):
    old = old_in_new_vocabulary(scheme)
    return [f for f in FIELDS if set(old[f]) != set(result.get(f) or [])]


def review_flags(scheme, result):
    """Reasons a scheme should be looked at first by NCSS: disability / mental health, abuse, retired old tags, empty output."""
    flags = []
    old_scheme_types = {t.lower() for t in scheme.get("scheme_type") or []}
    for term in ("covid-19 support", "abuse/family violence", "loss of breadwinner support"):
        if term in old_scheme_types:
            flags.append(f"old scheme_type: {term}")
    who = result.get("who_is_it_for") or []
    if "Persons with disabilities (PWDs)" in who or "Persons with mental health conditions" in who:
        flags.append("disability / mental health")
    if "Victims of abuse or harassment" in who:
        flags.append("victims of abuse")
    if not any(result.get(f) for f in FIELDS):
        flags.append("no tags")
    return flags


def term_counts(rows):
    """rows: iterable of {field: [terms]} -> {field: Counter}."""
    out = {f: Counter() for f in FIELDS}
    for row in rows:
        for f in FIELDS:
            out[f].update(set(row.get(f) or []))
    return out


def apply_plan(snapshot, results):
    """{id: {field: terms}} for schemes whose new tags differ from the stored ones (exact lists, not just the vocabulary).

    A field the model left empty never wipes existing tags: it gets the old tags translated to the current vocabulary
    instead, or stays as is when nothing translates (stuck_off_vocabulary lists those for a model re-ask)."""
    plan = {}
    for sid, scheme in snapshot.items():
        result = results.get(sid)
        if not result:
            continue
        old = old_in_new_vocabulary(scheme)
        update = {}
        for f in FIELDS:
            new = result.get(f) or old[f]
            if new and new != (scheme.get(f) or None):
                update[f] = new
        if update:
            plan[sid] = update
    return plan


def stuck_off_vocabulary(snapshot, plan):
    """[(id, field)] still holding terms outside the current vocabulary after the plan: re-ask with classify --ids --force."""
    stuck = []
    for sid, scheme in snapshot.items():
        for f in FIELDS:
            terms = plan.get(sid, {}).get(f) or scheme.get(f) or []
            if any(t not in tx.term_names(f) for t in terms):
                stuck.append((sid, f))
    return stuck


def stale_results(snapshot, results):
    """[(id, reason)] for results that must not be applied: made from other text or prompt than the snapshot holds, or from another vocabulary."""
    stale = []
    for sid, scheme in snapshot.items():
        result = results.get(sid)
        if not result:
            continue
        if result.get("taxonomy_version") != tx.TAXONOMY["version"]:
            stale.append((sid, "taxonomy_version"))
        elif result.get("input_hash") != input_hash(scheme):
            stale.append((sid, "input_hash"))
    return stale


def live_drift(snapshot_scheme, live):
    """True when the live doc no longer matches the snapshot the plan was made from (an edit landed in between)."""
    return input_hash(live) != input_hash(snapshot_scheme) or any((live.get(f) or None) != (snapshot_scheme.get(f) or None) for f in FIELDS)


def empty_over_existing(snapshot, results):
    """[(id, field)] where the model returned nothing but the scheme already has tags (kept as is by apply_plan)."""
    return [(sid, f) for sid, scheme in snapshot.items() if (result := results.get(sid))
            for f in FIELDS if not result.get(f) and scheme.get(f)]


# ------------------------------------------------------------------ io
def _read_jsonl(path):
    if not Path(path).exists():
        return {}
    return {r["id"]: r for r in (json.loads(l) for l in open(path) if l.strip())}


def _append_jsonl(path, row):
    with open(path, "a") as f:
        f.write(json.dumps(row, default=str) + "\n")


def _firestore(env):
    import firebase_admin
    from dotenv import dotenv_values
    from firebase_admin import credentials, firestore

    env_file, project = ENVS[env]
    e = dotenv_values(HERE / env_file)
    if e["FB_PROJECT_ID"] != project:  # explicit raise: an assert is stripped under python -O and this guards writes
        raise SystemExit(f"{env_file} points at {e['FB_PROJECT_ID']}, expected {project}")
    app = firebase_admin.initialize_app(credentials.Certificate({
        "type": e["FB_TYPE"], "project_id": e["FB_PROJECT_ID"], "private_key_id": e["FB_PRIVATE_KEY_ID"],
        "private_key": e["FB_PRIVATE_KEY"].replace("\\n", "\n"), "client_email": e["FB_CLIENT_EMAIL"],
        "client_id": e["FB_CLIENT_ID"], "auth_uri": e["FB_AUTH_URI"], "token_uri": e["FB_TOKEN_URI"]}), name=env)
    return firestore.client(app)


def cmd_snapshot(a):
    OUT.mkdir(parents=True, exist_ok=True)
    db = _firestore(a.env)
    docs = [(d.id, d.to_dict()) for d in db.collection("schemes").stream()]
    path = OUT / f"snapshot-{a.env}.jsonl"
    with open(path, "w") as f:
        for sid, d in docs:
            f.write(json.dumps({"id": sid, **{k: d.get(k) for k in SNAPSHOT_KEYS}}, default=str) + "\n")
    print(f"{a.env}: {len(docs)} schemes -> {path}")


def _snapshot(env="prod"):
    return _read_jsonl(OUT / f"snapshot-{env}.jsonl")


def cmd_classify(a):
    snapshot = _snapshot()
    results_path = OUT / "results.jsonl"
    results = _read_jsonl(results_path)
    ids = [l.strip() for l in open(a.ids)] if a.ids else list(snapshot)
    todo = [snapshot[i] for i in ids if i in snapshot and needs_classification(snapshot[i], results.get(i), a.force)]
    print(f"{len(snapshot)} schemes, {len(ids)} selected, {len(todo)} to classify")

    def run(scheme):
        t0 = time.time()
        for attempt in range(6):  # Azure token-per-minute limit: back off and retry
            try:
                raw = tagger.request_tags(scheme)
                break
            except Exception as err:  # noqa: BLE001
                if "429" not in str(err) or attempt == 5:
                    raise
                time.sleep(15 * (attempt + 1))
        return {"id": scheme["id"], "input_hash": input_hash(scheme), "model": os.getenv("AZURE_OPENAI_TAGGING_DEPLOYMENT", "gpt-6-luna"),
                "effort": tagger.TAGGING_EFFORT, "taxonomy_version": tx.TAXONOMY["version"], "latency": round(time.time() - t0, 1),
                **new_tags(raw)}

    done = failed = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for scheme, fut in [(s, ex.submit(run, s)) for s in todo]:
            try:
                _append_jsonl(results_path, fut.result())  # later lines supersede earlier ones for the same id
                done += 1
            except Exception as err:  # noqa: BLE001 - keep going; failed ids are retried on the next run
                failed += 1
                print("FAILED", scheme["id"], type(err).__name__, str(err)[:120])
    print(f"classified {done}, failed {failed} -> {results_path}")


def _latest_results():
    results = {}
    for l in open(OUT / "results.jsonl"):
        if l.strip():
            r = json.loads(l)
            results[r["id"]] = r
    return results


def cmd_report(a):
    snapshot, results = _snapshot(), _latest_results()
    rows = [(snapshot[i], r) for i, r in results.items() if i in snapshot]
    old = term_counts(old_in_new_vocabulary(s) for s, _ in rows)
    new = term_counts(r for _, r in rows)
    lines = [f"# Reclassification report — {tx.TAXONOMY['version']}", "",
             f"{len(rows)} of {len(snapshot)} schemes classified; changed: " +
             ", ".join(f"{f} {sum(1 for s, r in rows if f in changed_fields(s, r))}" for f in FIELDS), ""]
    for f in FIELDS:
        lines += [f"## {f}", "", "| term | old (v2 vocab) | new |", "|---|---|---|"]
        for term in sorted(set(old[f]) | set(new[f]), key=lambda t: -new[f][t]):
            lines.append(f"| {term} | {old[f][term]} | {new[f][term]} |")
        lines.append("")
    path = OUT / "report.md"
    path.write_text("\n".join(lines))
    print("wrote", path)


def cmd_xlsx(a):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    snapshot, results = _snapshot(), _latest_results()
    wb = Workbook()
    ws = wb.active
    ws.title = "Schemes"
    head = ["id", "scheme", "agency", "link", "status", "flags", "changed fields",
            "old who_is_it_for", "new who_is_it_for", "NCSS age group / profile",
            "old what_it_gives", "new what_it_gives", "NCSS intervention",
            "old scheme_type", "new scheme_type", "NCSS need", "model rationale", "NCSS correction / comment"]
    ws.append(head)
    rows = []
    for sid, r in results.items():
        s = snapshot.get(sid)
        if not s:
            continue
        flags = review_flags(s, r)
        rows.append((not flags, s.get("scheme") or "", sid, s, r, flags))
    rows.sort(key=lambda x: (x[0], x[1].lower()))  # flagged first
    join = lambda v: "; ".join(v or [])  # noqa: E731
    ext = set(tx.TAXONOMY["extension_profiles"])
    mark = lambda v: [f"{p} (Schemes SG extension)" if p in ext else p for p in v]  # noqa: E731
    for _, _, sid, s, r, flags in rows:
        pw, pi, pn = tx.parents("who_is_it_for", r["who_is_it_for"] or []), tx.parents("what_it_gives", r["what_it_gives"] or []), tx.parents("scheme_type", r["scheme_type"] or [])
        ws.append([sid, s.get("scheme"), s.get("agency"), s.get("link"), s.get("status") or "active", join(flags), join(changed_fields(s, r)),
                   join(s.get("who_is_it_for")), join(r["who_is_it_for"]), join(pw["age_group"] + mark(pw["profile"])),
                   join(s.get("what_it_gives")), join(r["what_it_gives"]), join(pi["intervention"]),
                   join(s.get("scheme_type")), join(r["scheme_type"]), join(pn["need"]), r.get("rationale"), ""])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    fill = PatternFill("solid", fgColor="FFF2CC")
    for row in ws.iter_rows(min_row=2, min_col=6, max_col=6):
        if row[0].value:
            row[0].fill = fill
    counts = wb.create_sheet("Term counts")
    counts.append(["field", "term", "old (v2 vocab)", "new", "provisional"])
    old = term_counts(old_in_new_vocabulary(snapshot[i]) for i in results if i in snapshot)
    new = term_counts(results[i] for i in results if i in snapshot)
    for f in FIELDS:
        for term in sorted(set(old[f]) | set(new[f]), key=lambda t: -new[f][t]):
            counts.append([f, term, old[f][term], new[f][term], "yes" if tx.is_provisional(f, term) else ""])
    ref = wb.create_sheet("Reference")
    ref.append(["field", "term", "definition", "NCSS parent(s)", "provisional", "note"])
    for f, keys in (("who_is_it_for", ("age_group", "profile")), ("what_it_gives", ("intervention",)), ("scheme_type", ("need",))):
        for t in tx.TAXONOMY[f]:
            ref.append([f, t["name"], t["definition"], join(mark([p for k in keys for p in t[k]])), "yes" if t["provisional"] else "", t["note"]])
    notes = wb.create_sheet("Read me")
    for line in ("Old = current tags translated into the v2 vocabulary. New = gpt-6-luna output, validated against the v2 vocabulary.",
                 "Parents (NCSS age group / profile, intervention, need) come from the static table, never from the model.",
                 "Flagged schemes are sorted first. Provisional = NCSS has not confirmed the parent yet.",
                 "Corrections: write them in the last column. We change the prompt or taxonomy, not individual rows."):
        notes.append([line])
    path = OUT / "ncss_review.xlsx"
    wb.save(path)
    print(f"wrote {path} ({len(rows)} schemes, {sum(1 for r in rows if r[5])} flagged)")


def cmd_apply(a):
    project = ENVS[a.env][1]
    if a.write and a.env == "prod" and a.confirm_project != project:  # explicit: a prod write must name the project
        sys.exit(f"prod write refused: pass --confirm-project {project}")
    snapshot, results = _snapshot(a.env), _latest_results()
    if not snapshot:  # classify ran on prod text; ids are identical while dev == prod
        sys.exit(f"take a {a.env} snapshot first: reclassify.py snapshot {a.env} (apply diffs against what {a.env} holds now)")
    stale = stale_results(snapshot, results)
    stale_ids = {sid for sid, _ in stale}
    plan = apply_plan(snapshot, {i: r for i, r in results.items() if i not in stale_ids})
    kept = empty_over_existing(snapshot, results)
    stuck = stuck_off_vocabulary(snapshot, plan)
    stuck_path = OUT / f"stuck-ids-{a.env}.txt"
    stuck_path.write_text("".join(f"{sid}\n" for sid in dict.fromkeys(sid for sid, _ in stuck)))
    print(f"{len(plan)} of {len(snapshot)} {a.env} schemes would change; {sum(1 for i in snapshot if i not in results)} have no result; "
          f"{len(stale)} stale results rejected {stale[:5]}; {len(kept)} empty model fields fall back to the old tags translated: {kept[:10]}; "
          f"{len(stuck)} fields still off-vocabulary {stuck[:10]} -> re-ask: classify --ids {stuck_path} --force")
    if not a.write:
        print("dry run (add --write to back up and write)")
        return
    if a.env == "dev":
        print("note: scheduled_firebase_collection_sync overwrites dev from prod twice a month and would revert this write; pause it for the review window")
    from firebase_admin import firestore

    db = _firestore(a.env)
    # Read each doc at write time: back up the LIVE tags and skip any doc edited since the snapshot.
    live_snaps = {d.id: d for d in db.get_all([db.collection("schemes").document(sid) for sid in plan]) if d.exists}
    live_docs = {sid: d.to_dict() for sid, d in live_snaps.items()}
    writable, drifted = {}, []
    for sid, update in plan.items():
        live = {"id": sid, **{k: (live_docs.get(sid) or {}).get(k) for k in SNAPSHOT_KEYS}}
        if sid not in live_docs or live_drift(snapshot[sid], live):
            drifted.append(sid)
        else:
            writable[sid] = update
    backup = OUT / f"backup-{a.env}-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    with open(backup, "w") as f:
        for sid in writable:
            f.write(json.dumps({"id": sid, **{k: live_docs[sid].get(k) for k in (*FIELDS, "tags_updated_at")}}, default=str) + "\n")
    print(f"backup of live tags -> {backup}; skipped {len(drifted)} docs changed or missing since the snapshot {drifted[:10]}")
    batch, n = db.batch(), 0
    for sid, update in writable.items():
        # precondition: an edit landing between this read and the commit fails the batch instead of being overwritten
        # (re-run snapshot + apply after such a failure: earlier batches stay written and are skipped as drifted)
        batch.update(db.collection("schemes").document(sid), {**update, "tags_updated_at": firestore.SERVER_TIMESTAMP},
                     option=db.write_option(last_update_time=live_snaps[sid].update_time))
        n += 1
        if n % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"wrote {n} schemes to {a.env} ({project})")


def cmd_restore(a):
    """Rollback: write the backed-up tags (and the previous tags_updated_at) back to each scheme in the backup file."""
    project = ENVS[a.env][1]
    rows = list(_read_jsonl(Path(a.backup)).values())
    print(f"{len(rows)} schemes in {a.backup} would be restored on {a.env} ({project})")
    if not a.write:
        print("dry run (add --write to restore)")
        return
    if a.env == "prod" and a.confirm_project != project:
        sys.exit(f"prod restore refused: pass --confirm-project {project}")
    from firebase_admin import firestore

    db = _firestore(a.env)
    batch, n = db.batch(), 0
    for row in rows:
        stamp = row.get("tags_updated_at")
        update = {f: row.get(f) for f in FIELDS}
        # backup stores str(datetime); write it back as a Timestamp so updated_since range queries still match
        update["tags_updated_at"] = datetime.fromisoformat(stamp) if stamp else firestore.DELETE_FIELD
        batch.update(db.collection("schemes").document(row["id"]), update)
        n += 1
        if n % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"restored {n} schemes on {a.env} ({project})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("snapshot"); p.add_argument("env", choices=["prod", "dev"]); p.set_defaults(fn=cmd_snapshot)
    p = sub.add_parser("classify"); p.add_argument("--ids"); p.add_argument("--force", action="store_true")
    p.add_argument("--workers", type=int, default=8); p.set_defaults(fn=cmd_classify)
    p = sub.add_parser("report"); p.set_defaults(fn=cmd_report)
    p = sub.add_parser("xlsx"); p.set_defaults(fn=cmd_xlsx)
    p = sub.add_parser("apply"); p.add_argument("env", choices=["dev", "prod"]); p.add_argument("--write", action="store_true")
    p.add_argument("--confirm-project", help="required with prod --write: the Firebase project id"); p.set_defaults(fn=cmd_apply)
    p = sub.add_parser("restore"); p.add_argument("env", choices=["dev", "prod"]); p.add_argument("backup"); p.add_argument("--write", action="store_true")
    p.add_argument("--confirm-project", help="required with prod --write: the Firebase project id"); p.set_defaults(fn=cmd_restore)
    args = ap.parse_args()
    args.fn(args)
