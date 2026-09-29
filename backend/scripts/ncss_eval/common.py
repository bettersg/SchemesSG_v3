"""Shared: frozen input text + prompt definitions."""
import json, os
from dotenv import load_dotenv
import taxonomy as tx

load_dotenv("../../scheme-processor/.env")
DATA = "data"


def load_sample(path=os.environ.get("SAMPLE", f"{DATA}/sample_dev_50.jsonl")):
    return [json.loads(l) for l in open(path)]


def frozen_state(s) -> str:
    """Identical text goes to every arm and to the gold labeller/reviewer: all descriptive fields."""
    parts = [f"Scheme: {s.get('scheme') or ''}", f"Agency: {s.get('agency') or ''}"]
    desc = (s.get("description") or "").strip()
    llm = (s.get("llm_description") or "").strip()
    if desc: parts.append(f"Description: {desc[:3500]}")
    if llm and llm != desc: parts.append(f"Detailed description: {llm[:3500]}")
    if s.get("summary") and str(s["summary"]).strip() not in (desc, llm): parts.append(f"Summary: {str(s['summary'])[:600]}")
    if s.get("eligibility"): parts.append(f"Eligibility: {str(s['eligibility'])[:1500]}")
    return "\n".join(parts)


def vocab(field):
    return {"who_is_it_for": tx.WHO_IS_IT_FOR, "what_it_gives": tx.WHAT_IT_GIVES, "scheme_type": tx.SCHEME_TYPE}[field]


def defs_block(field) -> str:
    return "\n".join(f"- {t.name}: {t.definition}" for t in vocab(field))
