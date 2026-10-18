"""10-category coverage: old dev tags + old mapping  vs  luna-medium scheme_type + v2 mapping (same schemes).
Lists schemes that DROP OUT of a category (and ones that join)."""
import json, glob
import taxonomy as tx
OLD = {
 "Financial Assistance": ["Financial Assistance","Low Income","COVID-19 Support"],
 "Family & Children": ["Family","Children","Youth","Youth-at-Risk","Single Parents","Women"],
 "Health & Wellbeing": ["Healthcare","Mental Health","End-of-Life/Palliative Care","Counselling and Emotional Support"],
 "Housing & Food": ["Housing/Shelter","Food Support"], "Education": ["Education Support"],
 "Employment & Training": ["Employment Support","Vocational Training","Ex-offender Support"],
 "Seniors & Caregiving": ["Elderly","Caregiver Support"],
 "Disability & Transport": ["Persons with Disabilities (PWD)","Special Needs","Transport Support"],
 "Legal & Safety": ["Legal Aid","Abuse/Family Violence"], "Community Support": ["General Public Support"]}
S = {json.loads(l)["id"]: json.loads(l) for l in open("data/sample_dev_50.jsonl")}
runs = {json.load(open(p))["id"]: json.load(open(p))["result"] for p in glob.glob("data/runs/luna-medium/*.json")}
def cats(types, mapping): return {c for c, ts in mapping.items() if set(types or []) & set(ts)}
tot = {c: [0, 0, 0, 0] for c in OLD}  # old, new, lost, gained
lost = {c: [] for c in OLD}; gained = {c: [] for c in OLD}; nocat_old = nocat_new = 0
for i, s in S.items():
    if i not in runs: continue
    o = cats(s.get("scheme_type"), OLD); n = cats(runs[i]["scheme_type"], tx.SCHEME_CATEGORY_MAPPING_V2)
    nocat_old += not o; nocat_new += not n
    for c in OLD:
        tot[c][0] += c in o; tot[c][1] += c in n
        if c in o and c not in n: tot[c][2] += 1; lost[c].append(s["scheme"][:45])
        if c in n and c not in o: tot[c][3] += 1; gained[c].append(s["scheme"][:45])
print(f"{'category':24s} old new lost gained"); 
for c, (o, n, l, g) in tot.items(): print(f"{c:24s} {o:3d} {n:3d} {l:4d} {g:6d}")
print(f"\nschemes in NO category: old={nocat_old} new={nocat_new} (of {len(runs)})")
for c in OLD:
    if lost[c]: print(f"\nLOST from {c}: " + "; ".join(lost[c][:8]))
