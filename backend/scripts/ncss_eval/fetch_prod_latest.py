"""READ-ONLY fetch from PROD Firestore (schemessg): N latest active schemes -> data/prod_latest<N>.jsonl (gitignored).
Active = status missing (legacy-active) or not in {inactive, retired}, same rule as reindex_embeddings.py. Latest = created_at, else approved_at."""
import json, os, sys
from dotenv import dotenv_values
import firebase_admin
from firebase_admin import credentials, firestore

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
RANDOM_EXCL = sys.argv[2] if len(sys.argv) > 2 else None  # optional: jsonl of already-picked ids -> random N from the rest (seed 406)
e = dotenv_values("../../functions/.env.prod")
assert e["FB_PROJECT_ID"] == "schemessg"
firebase_admin.initialize_app(credentials.Certificate({
    "type": e["FB_TYPE"], "project_id": e["FB_PROJECT_ID"], "private_key_id": e["FB_PRIVATE_KEY_ID"],
    "private_key": e["FB_PRIVATE_KEY"].replace("\\n", "\n"), "client_email": e["FB_CLIENT_EMAIL"],
    "client_id": e["FB_CLIENT_ID"], "auth_uri": e["FB_AUTH_URI"], "token_uri": e["FB_TOKEN_URI"]}))
db = firestore.client()
docs = [(d.id, d.to_dict()) for d in db.collection("schemes").stream()]
active = [(i, d) for i, d in docs if d.get("status") not in ("inactive", "retired")]
def ts(d):
    for k in ("created_at", "approved_at"):
        v = d.get(k)
        if v is not None: return v.timestamp() if hasattr(v, "timestamp") else 0
    return 0
active.sort(key=lambda x: ts(x[1]), reverse=True)
print("prod total", len(docs), "active", len(active), "with created_at/approved_at", sum(1 for _, d in active if ts(d) > 0))
if RANDOM_EXCL:
    import random
    seen = {json.loads(l)["id"] for l in open(RANDOM_EXCL)}
    rest = [x for x in active if x[0] not in seen]
    random.Random(406).shuffle(rest)
    pick = rest[:N]; tag = f"prod_random{N}"
else:
    pick = active[:N]; tag = f"prod_latest{N}"
os.makedirs("data", exist_ok=True)
F = ["scheme", "agency", "link", "description", "llm_description", "summary", "eligibility", "who_is_it_for", "what_it_gives", "scheme_type", "status", "created_at", "approved_at"]
with open(f"data/{tag}.jsonl", "w") as f:
    for i, d in pick: f.write(json.dumps({"id": i, **{k: d.get(k) for k in F}}, default=str) + "\n")
print("saved", tag, len(pick))
