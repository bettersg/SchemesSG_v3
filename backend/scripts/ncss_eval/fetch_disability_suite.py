"""READ-ONLY prod pull (schemessg) for the disability-vs-mental-health suite. Saves only the matched subset to data/ (gitignored)."""
import json, os, re
from dotenv import dotenv_values
import firebase_admin
from firebase_admin import credentials, firestore
e = dotenv_values("../../functions/.env.prod"); assert e["FB_PROJECT_ID"] == "schemessg"
firebase_admin.initialize_app(credentials.Certificate({"type": e["FB_TYPE"], "project_id": e["FB_PROJECT_ID"], "private_key_id": e["FB_PRIVATE_KEY_ID"],
    "private_key": e["FB_PRIVATE_KEY"].replace("\\n", "\n"), "client_email": e["FB_CLIENT_EMAIL"], "client_id": e["FB_CLIENT_ID"], "auth_uri": e["FB_AUTH_URI"], "token_uri": e["FB_TOKEN_URI"]}))
docs = [(d.id, d.to_dict()) for d in firestore.client().collection("schemes").stream()]
MH = re.compile(r"mental|psychiatr|depress|schizophren|anxiety|bipolar|psycholog|emotional|dementia|autis", re.I)
PWD = "Persons with disabilities (PWDs)"
def txt(d): return " ".join(str(d.get(k) or "") for k in ("scheme", "description", "llm_description", "summary", "eligibility"))
A = [(i, d) for i, d in docs if PWD in (d.get("who_is_it_for") or []) and MH.search(txt(d))]           # PWD-tagged + mental/condition words (issue #406 failure mode)
B = [(i, d) for i, d in docs if "Persons with mental health issues" in (d.get("who_is_it_for") or []) and PWD not in (d.get("who_is_it_for") or [])]  # mental-only in prod (leak check)
C = [(i, d) for i, d in docs if PWD in (d.get("who_is_it_for") or []) and not MH.search(txt(d))]      # plain PWD
print(len(docs), "A", len(A), "B", len(B), "C", len(C))
import random; random.seed(406)
pick = [("A", x) for x in random.sample(A, min(14, len(A)))] + [("B", x) for x in random.sample(B, min(10, len(B)))] + [("C", x) for x in random.sample(C, min(6, len(C)))]
keys = ["scheme", "agency", "description", "llm_description", "summary", "eligibility", "who_is_it_for", "status", "link", "what_it_gives", "scheme_type"]
with open("data/disability_suite_prod.jsonl", "w") as f:
    for g, (i, d) in pick: f.write(json.dumps({"id": i, "group": g, **{k: d.get(k) for k in keys}}, default=str) + "\n")
print("wrote", len(pick))
