"""Read-only: sample N random schemes from DEV Firestore (schemessg-v3-dev) -> frozen JSONL.
Refuses to run against any other project."""
import json, os, random, sys
from collections import Counter
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv("../../scheme-processor/.env")
assert os.environ["FB_PROJECT_ID"] == "schemessg-v3-dev", "dev only"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
cred = credentials.Certificate({
    "type": os.getenv("FB_TYPE"), "project_id": os.getenv("FB_PROJECT_ID"),
    "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FB_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FB_CLIENT_EMAIL"), "client_id": os.getenv("FB_CLIENT_ID"),
    "auth_uri": os.getenv("FB_AUTH_URI"), "token_uri": os.getenv("FB_TOKEN_URI"),
})
firebase_admin.initialize_app(cred)
db = firestore.client()
docs = [(d.id, d.to_dict()) for d in db.collection("schemes").stream()]
print("total docs", len(docs), "status", Counter(d.get("status") for _, d in docs))
ok = [(i, d) for i, d in docs if d.get("description") or d.get("llm_description")]
random.seed(406)
pick = random.sample(ok, min(N, len(ok)))
keys = ["scheme", "agency", "description", "llm_description", "summary", "eligibility", "how_to_apply",
        "who_is_it_for", "what_it_gives", "scheme_type", "search_booster", "service_area", "status", "link"]
os.makedirs("data", exist_ok=True)
with open("data/sample_dev_50.jsonl", "w") as f:
    for i, d in pick:
        f.write(json.dumps({"id": i, **{k: d.get(k) for k in keys}}, default=str) + "\n")
print("wrote", len(pick))
