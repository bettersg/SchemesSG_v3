"""No-gold comparison: luna v2 tags vs current PROD tags (renames/merges mapped). Usage: compare_prod.py <sample.jsonl> <rundir>"""
import json, sys, glob, collections as C
import taxonomy as tx
S = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[1])}
R = {r["id"]: r for r in (json.load(open(p)) for p in glob.glob(sys.argv[2] + "/*.json"))}
MERGED = {"Referral services": "Information and referral services", "Information services": "Information and referral services"}
def mig(v, f):
    o = {tx.RENAMES.get(x, x) for x in v or []}
    return {MERGED.get(x, x) for x in o} if f == "what_it_gives" else o
for f in ("who_is_it_for", "what_it_gives", "scheme_type"):
    voc = {t.name for t in tx.vocab(f)} if hasattr(tx, "vocab") else None
    pn = ln = 0; lo = C.Counter(); po = C.Counter(); both = C.Counter(); jac = []; gone = C.Counter()
    for i, r in R.items():
        p = mig(S[i].get(f), f); l = set(r["result"][f]); pn += len(p); ln += len(l)
        for t in l - p: lo[t] += 1
        for t in p - l: po[t] += 1
        for t in l & p: both[t] += 1
        jac.append(len(l & p) / max(1, len(l | p)))
    print(f"\n== {f}: avg prod {pn/len(R):.1f} / luna {ln/len(R):.1f} terms; mean Jaccard {sum(jac)/len(jac):.2f}")
    print(" luna-only top:", lo.most_common(8)); print(" prod-only top:", po.most_common(8))
allw = C.Counter(t for r in R.values() for t in r["result"]["what_it_gives"])
new = ["Information and referral services","Tuition","Enrichment programmes","Home retrofitting","Assistive technology","Learning intervention"]
print("\nnew/split what terms fired:", {t: allw.get(t, 0) for t in new})
print("prod terms no longer in vocab (who):", C.Counter(t for s in S.values() for t in mig(s.get("who_is_it_for"), "who_is_it_for") if t not in {x.name for x in tx.WHO_IS_IT_FOR}).most_common(15))
print("prod terms not in vocab (what):", C.Counter(t for s in S.values() for t in mig(s.get("what_it_gives"), "what_it_gives") if t not in {x.name for x in tx.WHAT_IT_GIVES}).most_common(10))
print("prod terms not in vocab (type):", C.Counter(t for s in S.values() for t in (s.get("scheme_type") or []) if t not in {x.name for x in tx.SCHEME_TYPE}).most_common(15))
