"""Per-term FP/FN listing for a field. usage: errors.py <field> [split]"""
import sys, json, glob
from collections import defaultdict
sys.argv = [sys.argv[0], "--split", sys.argv[2] if len(sys.argv) > 2 else "all"] + ["--field-x", sys.argv[1]] if False else sys.argv
field = sys.argv[1]; split = sys.argv[2] if len(sys.argv) > 2 else "all"
sys.argv = [sys.argv[0], "--split", split]
import score as sc
runs = sc.load("luna-medium"); ids = [i for i in runs if i in sc.gold and sc.keep(i)]
fp = defaultdict(list); fn = defaultdict(list)
for i in ids:
    p = sc.preds("luna-medium", runs[i], 0)[field]; g = set(sc.gold[i][field]); nm = sc.gold[i]["scheme"][:38]
    for t in p - g: fp[t].append(nm)
    for t in g - p: fn[t].append(nm)
print("FALSE POSITIVES"); [print(f"  {t} x{len(v)}: {'; '.join(v[:4])}") for t, v in sorted(fp.items(), key=lambda x: -len(x[1]))]
print("MISSES"); [print(f"  {t} x{len(v)}: {'; '.join(v[:4])}") for t, v in sorted(fn.items(), key=lambda x: -len(x[1]))]
