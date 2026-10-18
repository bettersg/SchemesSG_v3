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
  reclassify.py apply dev [--write]         dry-run by default; --write backs up the old tags then updates the 3 fields
Prod writes are refused here: they run only after NCSS + partner sign-off, from the frozen results file.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import types
from collections import Counter
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
    """Reasons a scheme should be looked at first by NCSS: sensitive terms, provisional parents, empty output."""
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
    for field in FIELDS:
        provisional = [t for t in result.get(field) or [] if tx.is_provisional(field, t)]
        if provisional:
            flags.append("provisional: " + ", ".join(provisional))
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
    """{id: {field: terms}} for schemes whose new tags differ from the stored ones (exact lists, not just the vocabulary)."""
    plan = {}
    for sid, scheme in snapshot.items():
        result = results.get(sid)
        if not result:
            continue
        update = {f: result[f] for f in FIELDS if (result.get(f) or None) != (scheme.get(f) or None)}
        if update:
            plan[sid] = update
    return plan


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
    assert e["FB_PROJECT_ID"] == project, f"{env_file} is not {project}"
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
    for _, _, sid, s, r, flags in rows:
        pw, pi, pn = tx.parents("who_is_it_for", r["who_is_it_for"] or []), tx.parents("what_it_gives", r["what_it_gives"] or []), tx.parents("scheme_type", r["scheme_type"] or [])
        ws.append([sid, s.get("scheme"), s.get("agency"), s.get("link"), s.get("status") or "active", join(flags), join(changed_fields(s, r)),
                   join(s.get("who_is_it_for")), join(r["who_is_it_for"]), join(pw["age_group"] + pw["profile"]),
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
    if a.env != "dev":
        sys.exit("prod writes are not wired here: they run after NCSS + partner sign-off (see docs/plans)")
    snapshot, results = _snapshot(a.env), _latest_results()
    if not snapshot:  # dev snapshot not taken: classify ran on prod text; ids are identical while dev == prod
        sys.exit("take a dev snapshot first: reclassify.py snapshot dev (apply diffs against what dev holds now)")
    plan = apply_plan(snapshot, results)
    print(f"{len(plan)} of {len(snapshot)} dev schemes would change; {sum(1 for i in snapshot if i not in results)} have no result")
    if not a.write:
        print("dry run (add --write to back up and write)")
        return
    db = _firestore("dev")
    backup = OUT / f"backup-dev-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    with open(backup, "w") as f:
        for sid in plan:
            f.write(json.dumps({"id": sid, **{k: snapshot[sid].get(k) for k in FIELDS}}) + "\n")
    print("backup of old tags ->", backup)
    batch, n = db.batch(), 0
    for sid, update in plan.items():
        batch.update(db.collection("schemes").document(sid), update)
        n += 1
        if n % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"wrote {n} schemes to dev")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("snapshot"); p.add_argument("env", choices=["prod", "dev"]); p.set_defaults(fn=cmd_snapshot)
    p = sub.add_parser("classify"); p.add_argument("--ids"); p.add_argument("--force", action="store_true")
    p.add_argument("--workers", type=int, default=8); p.set_defaults(fn=cmd_classify)
    p = sub.add_parser("report"); p.set_defaults(fn=cmd_report)
    p = sub.add_parser("xlsx"); p.set_defaults(fn=cmd_xlsx)
    p = sub.add_parser("apply"); p.add_argument("env", choices=["dev", "prod"]); p.add_argument("--write", action="store_true"); p.set_defaults(fn=cmd_apply)
    args = ap.parse_args()
    args.fn(args)
