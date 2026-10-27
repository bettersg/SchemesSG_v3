"""READ-ONLY fetch from PROD Firestore (schemessg). Saves only Care Corner-matching schemes to data/ (gitignored).
Never writes to Firestore."""
import json, os, re
from dotenv import dotenv_values
import firebase_admin
from firebase_admin import credentials, firestore

e = dotenv_values("../../functions/.env.prod")
assert e["FB_PROJECT_ID"] == "schemessg"
cred = credentials.Certificate({
    "type": e["FB_TYPE"], "project_id": e["FB_PROJECT_ID"], "private_key_id": e["FB_PRIVATE_KEY_ID"],
    "private_key": e["FB_PRIVATE_KEY"].replace("\\n", "\n"), "client_email": e["FB_CLIENT_EMAIL"],
    "client_id": e["FB_CLIENT_ID"], "auth_uri": e["FB_AUTH_URI"], "token_uri": e["FB_TOKEN_URI"]})
firebase_admin.initialize_app(cred)
db = firestore.client()
docs = [(d.id, d.to_dict()) for d in db.collection("schemes").stream()]
print("prod schemes total:", len(docs))
pat = re.compile(r"care\s*corner", re.I)
hits = [(i, d) for i, d in docs if any(pat.search(str(d.get(k) or "")) for k in ("agency",))]
by_field = {k: sum(1 for _, d in hits if pat.search(str(d.get(k) or ""))) for k in ("agency",)}
print("matches:", len(hits), by_field)
os.makedirs("data", exist_ok=True)
with open("data/carecorner_prod.jsonl", "w") as f:
    for i, d in hits:
        f.write(json.dumps({"id": i, **{k: d.get(k) for k in ["scheme", "agency", "link", "description", "llm_description", "summary", "eligibility", "who_is_it_for", "what_it_gives", "scheme_type", "status"]}}, default=str) + "\n")
for i, d in hits[:15]:
    print("-", d.get("agency"), "|", d.get("scheme"), "|", d.get("status"), "|", d.get("link"))
