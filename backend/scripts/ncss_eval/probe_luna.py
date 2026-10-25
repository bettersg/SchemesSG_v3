"""Probe: does the Azure gpt-6-luna deployment honour json_schema + reasoning_effort?"""
import json, os, sys
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv("../../scheme-processor/.env")
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ.get("OPENAI_API_VERSION", "2025-01-01-preview"),
)
DEPLOY = sys.argv[1] if len(sys.argv) > 1 else "gpt-6-luna"
schema = {"name": "t", "strict": True, "schema": {
    "type": "object", "additionalProperties": False, "required": ["who"],
    "properties": {"who": {"type": "array", "items": {"type": "string", "enum": ["Seniors", "Adults", "Youths", "Children"]}}}}}
for effort in ["low", "medium", "high"]:
    try:
        r = client.chat.completions.create(
            model=DEPLOY, reasoning_effort=effort, max_completion_tokens=4000,
            response_format={"type": "json_schema", "json_schema": schema},
            messages=[{"role": "user", "content": "A programme for people aged 65 and above and children aged 8. Return who it is for."}])
        u = r.usage
        rt = getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", None)
        print(effort, "OK", r.choices[0].message.content, "completion_tokens", u.completion_tokens, "reasoning_tokens", rt)
    except Exception as e:
        print(effort, "ERR", type(e).__name__, str(e)[:300])
