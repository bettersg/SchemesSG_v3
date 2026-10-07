"""Disability vs mental-health suite. Reads runs for probes + prod-suite; reports PWD / mental-health P/R and hard-violation list.
usage: score_suite.py <run-dir-suffix e.g. -suite>"""
import glob, json, sys
tag = sys.argv[1] if len(sys.argv) > 1 else "-suite"
import taxonomy as tx
PARENT = {t.name: set(t.profile) for t in tx.WHO_IS_IT_FOR}
def rolls(terms, prof):  # NCSS roll-up: granular term counts if its parent profile matches (autism/special needs -> PWD)
    return any(prof in PARENT.get(t, ()) for t in terms)
PWD, MH = "Persons with disabilities", "Persons with mental health conditions"
gold = {g["id"]: g for f in ("data/probes_gold.json", "data/disability_suite_gold.json") for g in json.load(open(f))} if True else {}
runs = {json.load(open(p))["id"]: json.load(open(p)) for p in glob.glob(f"data/runs/luna-medium{tag}/*.json")}
def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 1.0; r = tp / (tp + fn) if tp + fn else 1.0; return p, r
for name, term, key in (("PWD", PWD, "pwd"), ("Mental health", MH, "mental_health")):
    tp = fp = fn = 0
    for i, g in gold.items():
        if i not in runs: continue
        pred = rolls(runs[i]["result"]["who_is_it_for"], term)
        tp += pred and g[key]; fp += pred and not g[key]; fn += (not pred) and g[key]
    p, r = prf(tp, fp, fn); print(f"{name:14s} P={p:.2f} R={r:.2f} tp={tp} fp={fp} fn={fn}")
print("\nHARD VIOLATIONS (mental-health-only tagged PWD):")
n = 0
for i, g in gold.items():
    if i in runs and rolls(runs[i]["result"]["who_is_it_for"], PWD) and g["mental_health"] and not g["pwd"]:
        n += 1; print("  ", g["scheme"], "|", g["reason"][:100])
print("  count", n)
print("\nOTHER MISMATCHES:")
for i, g in gold.items():
    if i not in runs: continue
    w = runs[i]["result"]["who_is_it_for"]; pp, pm = rolls(w, PWD), rolls(w, MH)
    if pp != g["pwd"] or pm != g["mental_health"]:
        print(f"   {g['scheme'][:55]:55s} gold pwd={g['pwd']} mh={g['mental_health']} | luna pwd={pp} mh={pm} | {g['reason'][:70]}")
