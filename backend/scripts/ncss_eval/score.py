"""Score arms vs gold. usage: score.py [--jev-threshold 0.5] [--gold data/gold_draft.json]
Micro P/R/F1 per field, per-term counts, review-queue size (Jev band), rule checks, cost/latency."""
import argparse, glob, json, os
from collections import defaultdict
import common as c
import taxonomy as tx

ap = argparse.ArgumentParser()
ap.add_argument("--gold", default="data/gold_draft.json")
ap.add_argument("--split", choices=["dev", "test", "all"], default="all")
ap.add_argument("--include-excluded", action="store_true")
ap.add_argument("--jev-threshold", type=float, default=0.5)
ap.add_argument("--band", type=float, default=0.2, help="review band half-width around threshold")
a = ap.parse_args()
def fix_age(terms, amin, amax):
    d = tx.age_terms(amin, amax)
    if d is None: return set(terms)
    if amax is None and (amin is None or amin < 60) and "Seniors" not in terms:
        d = d - {"Seniors"}  # open-ended 'N+' does not imply seniors unless the tagger/labeller said so
    elif amax is None and (amin is None or amin < 60):
        d = d | {"Seniors"}
    return (set(terms) - tx.AGE_TERM_NAMES) | d

gold = {g["id"]: g for g in json.load(open(a.gold))}
MERGED = {"Referral services": "Information and referral services", "Information services": "Information and referral services"}
DROPPED_WHAT = {"Tuition/Enrichment programmes", "Home retrofitting and assistive technology", "Child protection services",
                "Protection against violence", "Identification and safety tagging", "COVID-19 support"}  # need relabel under v2
def migrate(vals, field):
    out = [tx.RENAMES.get(v, v) for v in vals]
    if field == "what_it_gives":
        out = [MERGED.get(v, v) for v in out if v not in DROPPED_WHAT]
    return sorted(set(out))
for g in gold.values():
    for f in ("who_is_it_for", "what_it_gives", "scheme_type"):
        g[f] = migrate(g[f], f)
for g in gold.values():  # gold age terms derived from stated range where one exists
    g["who_is_it_for"] = sorted(fix_age(g["who_is_it_for"], g.get("age_min"), g.get("age_max")))

FIELDS = ["who_is_it_for", "what_it_gives", "scheme_type"]
# no defensible label (vague/contradictory text) or moved to the disability suite -> excluded from headline metric
EXCLUDE = ("CDAC-SFCCA", "Viriya Mental", "MWS Active Ageing", "Friends @ St Hilda", "Care Corner Senior Care Centre (Toa", "Medisave Care")
SPLIT = json.load(open("data/split.json"))
def keep(i):
    if a.split != "all" and i not in SPLIT[a.split]: return False
    return a.include_excluded or not gold[i]["scheme"].startswith(EXCLUDE)

def load(arm):
    return {json.load(open(p))["id"]: json.load(open(p)) for p in glob.glob(f"data/runs/{arm}/*.json")}

def preds(arm, d, thr):
    if arm.startswith("luna"):
        out = {f: set(d["result"][f]) for f in FIELDS}
        out["who_is_it_for"] = fix_age(out["who_is_it_for"], d["result"].get("age_min"), d["result"].get("age_max"))
        return out
    out = {f: set() for f in FIELDS}
    for k, p in d["probs"].items():
        f, t = k.split("::", 1)
        if p >= thr: out[f].add(t)
    return out

def review_count(d, thr, band):
    return sum(1 for p in d["probs"].values() if thr - band < p < thr + band)

def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)

def rules(pred, g, d):
    """Rule checks return list of violations."""
    v = []
    who = pred["who_is_it_for"]
    if "Persons with disabilities (PWDs)" in who and "Persons with mental health conditions" in g["who_is_it_for"] \
            and "Persons with disabilities (PWDs)" not in g["who_is_it_for"]:
        v.append("mental-health-as-disability")
    if who & set(tx.MOVED_OUT_OF_WHO): v.append("moved-out who term")
    if set(pred["scheme_type"]) & set(tx.REMOVED_FROM_SCHEME_TYPE): v.append("pop term in scheme_type")
    return v

def report(arm, thr=None):
    runs = load(arm); ids = [i for i in runs if i in gold and keep(i)]
    if not ids: return
    res = {}
    thr = thr if thr is not None else a.jev_threshold
    print(f"\n=== {arm}  n={len(ids)}" + (f" thr={thr}" if not arm.startswith('luna') else ""))
    viol = 0
    for f in FIELDS:
        tp = fp = fn = 0; per = defaultdict(lambda: [0, 0, 0])
        for i in ids:
            p = preds(arm, runs[i], thr)[f]; g = set(gold[i][f])
            for t in p & g: tp += 1; per[t][0] += 1
            for t in p - g: fp += 1; per[t][1] += 1
            for t in g - p: fn += 1; per[t][2] += 1
        P, R, F = prf(tp, fp, fn); res[f] = (P, R, F)
        print(f"  {f:15s} P={P:.2f} R={R:.2f} F1={F:.2f}  tp={tp} fp={fp} fn={fn}")
        if f == "who_is_it_for":
            for label, sel in (("age terms", lambda t: t in tx.AGE_TERM_NAMES), ("profile terms", lambda t: t not in tx.AGE_TERM_NAMES)):
                t1 = f1 = n1 = 0
                for i in ids:
                    p = {t for t in preds(arm, runs[i], thr)[f] if sel(t)}; g = {t for t in gold[i][f] if sel(t)}
                    t1 += len(p & g); f1 += len(p - g); n1 += len(g - p)
                P2, R2, F2 = prf(t1, f1, n1); print(f"    {label:14s} P={P2:.2f} R={R2:.2f} F1={F2:.2f}  tp={t1} fp={f1} fn={n1}")
    for i in ids:
        v = rules(preds(arm, runs[i], thr), gold[i], runs[i])
        if v: viol += 1; print("  RULE VIOLATION", gold[i]["scheme"][:50], v)
    lat = sum(runs[i]["latency"] for i in ids) / len(ids)
    if arm.startswith("luna"):
        pt = sum(runs[i]["prompt_tokens"] for i in ids) / len(ids); ct = sum(runs[i]["completion_tokens"] for i in ids) / len(ids)
        print(f"  latency {lat:.1f}s  tokens/scheme in={pt:.0f} out={ct:.0f}")
    else:
        rq = sum(review_count(runs[i], thr, a.band) for i in ids) / len(ids)
        print(f"  latency {lat:.1f}s  review-band questions/scheme={rq:.1f}")
    print(f"  rule violations: {viol}")

def per_term(arm, thr):
    runs = load(arm); ids = [i for i in runs if i in gold and keep(i)]
    print(f"\n--- per-term who_is_it_for ({arm})")
    per = defaultdict(lambda: [0, 0, 0])
    for i in ids:
        p = preds(arm, runs[i], thr)["who_is_it_for"]; g = set(gold[i]["who_is_it_for"])
        for t in p & g: per[t][0] += 1
        for t in p - g: per[t][1] += 1
        for t in g - p: per[t][2] += 1
    for t, (tp, fp, fn) in sorted(per.items(), key=lambda x: -(x[1][0] + x[1][2])):
        p, r, f = prf(tp, fp, fn); print(f"  {t[:45]:45s} tp={tp} fp={fp} fn={fn} F1={f:.2f}")

if __name__ == "__main__":
    for arm in sorted(os.listdir("data/runs")):
        report(arm)
