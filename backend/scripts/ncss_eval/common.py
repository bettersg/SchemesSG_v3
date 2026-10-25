"""Shared: frozen input text + prompt definitions."""
import json, os
from dotenv import load_dotenv
import sys, types
import taxonomy as tx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../scheme-processor"))
sys.modules.setdefault("loguru", types.SimpleNamespace(logger=types.SimpleNamespace(error=print, warning=print, info=print)))
from app.services import taxonomy_tagger as tagger  # noqa: E402

load_dotenv("../../scheme-processor/.env")
DATA = "data"


def load_sample(path=os.environ.get("SAMPLE", f"{DATA}/sample_dev_50.jsonl")):
    return [json.loads(l) for l in open(path)]


def frozen_state(s) -> str:
    """Identical text goes to every arm and to the gold labeller/reviewer: the production tagger's own input builder,
    so the eval measures the input shape production sends."""
    return tagger.build_user_text(s)


def vocab(field):
    return {"who_is_it_for": tx.WHO_IS_IT_FOR, "what_it_gives": tx.WHAT_IT_GIVES, "scheme_type": tx.SCHEME_TYPE}[field]


def defs_block(field) -> str:
    return "\n".join(f"- {t.name}: {t.definition}" for t in vocab(field))
