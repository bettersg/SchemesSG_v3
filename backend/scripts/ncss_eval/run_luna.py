"""Arm A: gpt-6-luna, strict json_schema (enum-constrained), definitions in prompt.
usage: run_luna.py <effort> [deployment]   -> data/runs/luna-<effort>/<id>.json"""
import json, os, sys, time, types
from concurrent.futures import ThreadPoolExecutor
from openai import AzureOpenAI
import common as c

effort = sys.argv[1]
deploy = sys.argv[2] if len(sys.argv) > 2 else "gpt-6-luna"
out = f"{c.DATA}/runs/luna-{effort}" + os.environ.get("RUN_TAG", ""); os.makedirs(out, exist_ok=True)
client = AzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"], azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
                     api_version=os.environ.get("OPENAI_API_VERSION", "2025-01-01-preview"))

# Prompt and schema come from the production tagger so the gate measures exactly what ships.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scheme-processor"))
sys.modules.setdefault("loguru", types.SimpleNamespace(logger=types.SimpleNamespace(error=print, warning=print, info=print)))
from app.services.taxonomy_tagger import TAGGING_SCHEMA as SCHEMA, build_system_prompt  # noqa: E402
SYSTEM = build_system_prompt()

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
