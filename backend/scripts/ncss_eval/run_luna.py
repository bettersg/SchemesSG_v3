"""Arm A: gpt-6-luna, strict json_schema (enum-constrained), definitions in prompt.
usage: run_luna.py <effort> [deployment]   -> data/runs/luna-<effort>/<id>.json"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from openai import AzureOpenAI
import common as c

effort = sys.argv[1]
deploy = sys.argv[2] if len(sys.argv) > 2 else "gpt-6-luna"
out = f"{c.DATA}/runs/luna-{effort}" + os.environ.get("RUN_TAG", ""); os.makedirs(out, exist_ok=True)
client = AzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"], azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                     api_version=os.environ.get("OPENAI_API_VERSION", "2025-01-01-preview"))

MAXN = {"who_is_it_for": 8, "what_it_gives": 6, "scheme_type": 4}  # age terms are re-derived in code, so who has headroom

def arr(field):
    return {"type": "array", "maxItems": MAXN[field], "items": {"type": "string", "enum": [t.name for t in c.vocab(field)]}}

SCHEMA = {"name": "ncss_tags", "strict": True, "schema": {
    "type": "object", "additionalProperties": False,
    "required": ["who_is_it_for", "what_it_gives", "scheme_type", "age_min", "age_max", "rationale"],
    "properties": {"who_is_it_for": arr("who_is_it_for"), "what_it_gives": arr("what_it_gives"), "scheme_type": arr("scheme_type"),
                   "age_min": {"type": ["integer", "null"]}, "age_max": {"type": ["integer", "null"]},
                   "rationale": {"type": "string"}}}}

SYSTEM = f"""You tag Singapore social-service schemes using the NCSS-aligned taxonomy below. Select ALL applicable terms per field, only if the text supports them; do not guess.
Rules:
- Mental health conditions are NOT disabilities. Only permanent intellectual/physical disabilities count as "Persons with disabilities (PWDs)".
- Use "General public" only when no other who_is_it_for term fits.
- Age: report the stated age range in age_min/age_max (null if none or open-ended). Age terms are re-derived in code from the range (every overlapping band is tagged), so also select age terms consistent with the range: Infants and toddlers 0-3; Preschool 4-6; Primary 7-12; Children = umbrella 0-12; Teenagers 13-17; Youth = umbrella 13-21; Adults 22-59; Elderly 60+. Select EVERY band the range overlaps (e.g. 18+ => Youth, Adults, Elderly). When only a group is named (e.g. 'children') without ages, pick the best-matching terms.
- Precision over recall: tag only what the scheme clearly targets/provides as a main focus. Skip marginal or passing mentions. Most schemes need 2-5 who terms, 2-5 what terms, 1-3 scheme_type terms; hard caps are enforced.
- age_min/age_max: the ages of PARTICIPANTS/BENEFICIARIES only. Ignore ages of volunteers, staff, professionals or eligibility of referrers. If the text says 'N and above', set age_min=N and age_max=null. Select an age term for 'Elderly' only if the scheme targets seniors (60+) explicitly or age_min >= 60.
- rationale: one or two sentences.

WHO_IS_IT_FOR terms:
{c.defs_block('who_is_it_for')}

WHAT_IT_GIVES terms:
{c.defs_block('what_it_gives')}

SCHEME_TYPE terms (needs addressed):
{c.defs_block('scheme_type')}"""

def run(s):
    p = f"{out}/{s['id']}.json"
    if os.path.exists(p): return
    t0 = time.time()
    r = client.chat.completions.create(model=deploy, reasoning_effort=effort, max_completion_tokens=8000,
        response_format={"type": "json_schema", "json_schema": SCHEMA},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": c.frozen_state(s)}])
    u = r.usage
    json.dump({"id": s["id"], "result": json.loads(r.choices[0].message.content), "latency": time.time() - t0,
               "prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens}, open(p, "w"))

with ThreadPoolExecutor(6) as ex:
    list(ex.map(run, c.load_sample()))
print("done", out)
