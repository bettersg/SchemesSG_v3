"""Legacy search benchmark — reproduces the pre-Azure V3 stack on the current corpus.

Old stack (git ~9850fcc, Aug 2025): local all-mpnet transformer (768d, mean-pool +
L2-normalize) -> FAISS cosine (inner product on normalized vecs) -> rank by raw
similarity. NO BM25 rerank (that was added later with the Firestore migration).

To make it a fair A/B against the current benchmark, we do not use the stale 405-scheme
Aug-2025 FAISS index. Instead we re-embed the current production schemes with the old model
over the SAME text the current pipeline embeds (build_desc_booster), build a fresh
in-memory FAISS index, and score against the SAME gold set (benchmark_queries.py).

So the only things that differ from run_search_benchmark.py are: (a) embedding model
mpnet-768 vs Azure-2048, and (b) vector-only vs hybrid (0.7 vec + 0.3 bm25). Corpus,
queries, and gold labels are identical -> differences reflect the search change, not data.

Usage:
    cd backend
    uv run --with "numpy<2" --with torch --with transformers --with faiss-cpu \
        scripts/run_search_benchmark_legacy.py

Reads functions/.env.prod (Firebase only; no Azure needed). READ-ONLY.
"""

import csv
import os
import time
from pathlib import Path


os.environ["KMP_DUPLICATE_LIB_OK"] = "True"  # torch + faiss both bundle libomp; matches old searchModelManager

import firebase_admin
import numpy as np
import torch
from benchmark_queries import QUERIES
from dotenv import load_dotenv
from firebase_admin import credentials, firestore


BACKEND = Path(__file__).resolve().parents[1]

ML = BACKEND / "functions" / "ml_logic"
MODEL_PATH = ML / "schemesv2-torch-allmpp-model"
TOKENIZER_PATH = ML / "schemesv2-torch-allmpp-tokenizer"
KS = [1, 3, 5, 10]
PROD_PROJECT_ID = "schemessg"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_prod_environment() -> None:
    env_file = BACKEND / "functions" / ".env.prod"
    if not load_dotenv(env_file, override=True):
        raise RuntimeError(f"Unable to load production environment: {env_file}")
    if os.getenv("FB_PROJECT_ID") != PROD_PROJECT_ID:
        raise RuntimeError(f"Legacy benchmark must use {PROD_PROJECT_ID}")


def prod_db():
    cred = credentials.Certificate(
        {
            "type": require_env("FB_TYPE"),
            "project_id": require_env("FB_PROJECT_ID"),
            "private_key_id": require_env("FB_PRIVATE_KEY_ID"),
            "private_key": require_env("FB_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": require_env("FB_CLIENT_EMAIL"),
            "client_id": require_env("FB_CLIENT_ID"),
            "auth_uri": require_env("FB_AUTH_URI"),
            "token_uri": require_env("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": require_env("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": require_env("FB_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FB_UNIVERSE_DOMAIN", "googleapis.com"),
        }
    )
    return firestore.client(firebase_admin.initialize_app(cred, name="legacy_bench"))


def build_desc_booster(data):
    """Same field concatenation the current populate_embeddings.py uses."""
    parts = []
    for f in ["scheme", "agency", "llm_description", "search_booster", "who_is_it_for",
              "what_it_gives", "scheme_type", "service_area"]:
        v = data.get(f)
        if v is None:
            continue
        parts.append(", ".join(str(x) for x in v) if isinstance(v, list) else str(v))
    return " ".join(parts)


class OldEmbedder:
    """Local all-mpnet: mean-pooling + L2 normalize, exactly as old searchModelManager."""

    def __init__(self):
        from transformers import AutoModel, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(str(TOKENIZER_PATH))
        self.model = AutoModel.from_pretrained(str(MODEL_PATH))
        self.model.eval()

    @staticmethod
    def _mean_pool(out, mask):
        te = out[0]
        m = mask.unsqueeze(-1).expand(te.size()).float()
        return torch.sum(te * m, 1) / torch.clamp(m.sum(1), min=1e-9)

    def embed(self, texts, batch=32):
        vecs = []
        for i in range(0, len(texts), batch):
            chunk = texts[i : i + batch]
            enc = self.tok(chunk, padding=True, truncation=True, return_tensors="pt")
            with torch.no_grad():
                out = self.model(**enc)
            v = self._mean_pool(out, enc["attention_mask"])
            v = torch.nn.functional.normalize(v, p=2, dim=1)
            vecs.append(v.numpy().astype("float32"))
        return np.vstack(vecs)


def eval_binary(ranked_ids, relevant_ids, ks):
    rel = [1 if i in relevant_ids else 0 for i in ranked_ids]
    total = len(relevant_ids)
    out = {}
    for k in ks:
        hits = sum(rel[:k])
        out[f"P@{k}"] = hits / k
        out[f"R@{k}"] = hits / total if total else 0.0
    return out


def main():
    import faiss

    load_prod_environment()
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = Path(__file__).resolve().parent / "benchmark_out"
    outdir.mkdir(exist_ok=True)

    print(f"[LEGACY] connecting to prod ({os.getenv('FB_PROJECT_ID')}) [READ-ONLY] ...")
    db = prod_db()

    print("[LEGACY] loading old all-mpnet model ...")
    emb = OldEmbedder()

    print("[LEGACY] reading today's schemes + building desc_booster ...")
    ids, texts = [], []
    for d in db.collection("schemes").stream():
        data = d.to_dict()
        ids.append(d.id)
        texts.append(build_desc_booster(data))
    print(f"  {len(ids)} schemes. Re-embedding with old model (768d) ...")

    doc_vecs = emb.embed(texts)
    index = faiss.IndexFlatIP(doc_vecs.shape[1])  # inner product on normalized = cosine
    index.add(doc_vecs)
    print(f"  fresh in-memory FAISS index built: {index.ntotal} x {index.d}")

    def search(query, top_k=100):
        qv = emb.embed([query])
        _, idxs = index.search(qv, top_k)
        return [ids[j] for j in idxs[0] if j != -1]

    specific = [q for q in QUERIES if q["tier"] == "specific"]
    per_query = []
    for q in specific:
        gold = set(q.get("gold_relevant", []))
        ranked = search(q["query"])
        m = eval_binary(ranked, gold, KS)
        per_query.append({"id": q["id"], "query": q["query"], "n_gold": len(gold), "gold": m})

    # ---- per-query + average
    print("\n" + "=" * 78)
    print("LEGACY (old mpnet + FAISS, vector-only) — GOLD, specific queries")
    print("=" * 78)
    hdr = f"{'id':<5}{'query':<44}" + "".join(f"P@{k:<4}R@{k:<4}" for k in KS)
    print(hdr)
    print("-" * len(hdr))
    for pq in per_query:
        g = pq["gold"]
        print(f"{pq['id']:<5}{pq['query'][:43]:<44}" + "".join(f"{g[f'P@{k}']:<5.2f}{g[f'R@{k}']:<5.2f}" for k in KS))
    print("-" * len(hdr))

    def avg(metric):
        return float(np.mean([pq["gold"][metric] for pq in per_query]))

    print(f"{'AVG':<5}{'(macro-average)':<44}" + "".join(f"{avg(f'P@{k}'):<5.2f}{avg(f'R@{k}'):<5.2f}" for k in KS))

    summary = {}
    for k in KS:
        summary[f"P@{k}"] = avg(f"P@{k}")
        summary[f"R@{k}"] = avg(f"R@{k}")

    with open(outdir / f"legacy_summary_{ts}.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["metric", "value"])
        for k, v in summary.items():
            w.writerow([k, f"{v:.4f}"])
    print(f"\nWrote: {outdir / f'legacy_summary_{ts}.csv'}")


if __name__ == "__main__":
    main()
