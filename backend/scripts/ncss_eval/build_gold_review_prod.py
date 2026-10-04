"""Build data/gold_review_prod.csv: 30 latest + 30 random prod schemes, luna-medium tags prefilled for the reviewer to correct.
Random pick (seed 406), NOT disagreement-biased, so the result can be used for P/R. Also writes data/vocab_reference.txt."""
import csv, json, glob, random
import common as c, taxonomy as tx
MERGED = {"Referral services": "Information and referral services", "Information services": "Information and referral services"}
def mig(v, f):
    o = [tx.RENAMES.get(x, x) for x in v or []]
    return sorted({MERGED.get(x, x) for x in o} if f == "what_it_gives" else set(o))
rows = []
for path, runs, tag in (("data/prod_latest100.jsonl", "data/runs/luna-medium-prod100", "latest"),
                        ("data/prod_random100.jsonl", "data/runs/luna-medium-prodrand100", "random")):
    S = [json.loads(l) for l in open(path)]
    R = {r["id"]: r for r in (json.load(open(p)) for p in glob.glob(runs + "/*.json"))}
    random.Random(406).shuffle(S)
    for s in S[:30]:
        r = R[s["id"]]["result"]
        agree = {f: len(set(r[f]) & set(mig(s.get(f), f))) / max(1, len(set(r[f]) | set(mig(s.get(f), f)))) for f in ("who_is_it_for", "what_it_gives")}
        rows.append({"id": s["id"], "sample": tag, "scheme": s["scheme"], "agency": s["agency"], "link": s.get("link"),
                     "text": c.frozen_state(s)[:2200],
                     "luna_who": "; ".join(r["who_is_it_for"]), "luna_what": "; ".join(r["what_it_gives"]), "luna_type": "; ".join(r["scheme_type"]),
                     "age_min": r["age_min"], "age_max": r["age_max"], "luna_rationale": r["rationale"],
                     "prod_who": "; ".join(mig(s.get("who_is_it_for"), "who_is_it_for")), "prod_what": "; ".join(mig(s.get("what_it_gives"), "what_it_gives")),
                     "prod_type(old, FYI)": "; ".join(s.get("scheme_type") or []),
                     "agree_who": f"{agree['who_is_it_for']:.2f}", "agree_what": f"{agree['what_it_gives']:.2f}",
                     "REVIEW: ok / corrected / unsure": "", "corrected_who": "", "corrected_what": "", "corrected_type": "", "comment": ""})
with open("data/gold_review_prod.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open("data/vocab_reference.txt", "w") as f:
    for name, fld in (("WHO_IS_IT_FOR", "who_is_it_for"), ("WHAT_IT_GIVES", "what_it_gives"), ("SCHEME_TYPE", "scheme_type")):
        f.write(f"## {name}\n" + c.defs_block(fld) + "\n\n")
print(len(rows), "rows")
