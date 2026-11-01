"""Arm B: Jev (pinned jev-1.13.0), one Noul per term, per field. Raw probabilities saved; thresholds applied in score.py.
usage: run_jev.py   -> data/runs/jev/<id>.json  ({field: {term: prob}})"""
import json, os, sys, time
import httpx
import common as c

URL = "https://api.typesafe.ai/v1/systemone"
KEY = os.environ["JEV_API_KEY"]
MODEL = "jev-1.13.0"
out = f"{c.DATA}/runs/jev"; os.makedirs(out, exist_ok=True)

def question(field, t):
    if field == "who_is_it_for":
        ins = f"Is this scheme intended for or open to: {t.name}? Definition: {t.definition}"
    elif field == "what_it_gives":
        ins = f"Does this scheme provide: {t.name}? Definition: {t.definition}"
    else:
        ins = f"Does this scheme address the need area: {t.name}? Definition: {t.definition}"
    return {"type": "noul", "instructions": ins}

QS = {f"{f}::{t.name}": question(f, t) for f in ("who_is_it_for", "what_it_gives", "scheme_type") for t in c.vocab(f)}
CHUNK = int(sys.argv[1]) if len(sys.argv) > 1 else len(QS)

with httpx.Client(timeout=120) as h:
    for s in c.load_sample():
        p = f"{out}/{s['id']}.json"
        if os.path.exists(p): continue
        state = c.frozen_state(s); res = {}; toks = [0, 0]; t0 = time.time()
        items = list(QS.items())
        for i in range(0, len(items), CHUNK):
            body = {"state": state, "model": MODEL, "questions": dict(items[i:i + CHUNK])}
            for attempt in range(5):
                r = h.post(URL, json=body, headers={"Authorization": f"Bearer {KEY}"})
                if r.status_code in (429, 529): time.sleep(2 ** attempt); continue
                break
            r.raise_for_status(); j = r.json()
            assert j["model"] == MODEL, j["model"]
            for k, a in j["answers"].items(): res[k] = a["noul"]
            toks[0] += j["usage"]["input_tokens"]; toks[1] += j["usage"]["output_tokens"]
        json.dump({"id": s["id"], "probs": res, "latency": time.time() - t0, "input_tokens": toks[0], "output_tokens": toks[1]}, open(p, "w"))
print("done", out, "questions/scheme", len(QS))
