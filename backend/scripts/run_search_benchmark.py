"""Search-retrieval benchmark for SchemesSG, run top-to-bottom against PROD (read-only).

Reproduces the legacy REST production search path:
    query -> Azure text-embedding-3-large (2048d)
          -> Firestore find_nearest (COSINE) on schemes_embeddings
          -> BM25 rerank on search_booster
          -> combined = 0.7 * vec_norm + 0.3 * bm25

and scores it with set-retrieval metrics at K = 1,3,5,10 (order within top K ignored):
    Precision@K  — of the top K, fraction relevant
    Recall@K     — of all relevant schemes, fraction captured in top K

Primary relevance uses manually curated scheme IDs that are independent of the
search engine. A secondary category-derived pool is reported only as a weaker,
partly circular signal.

Usage:
    uv run scripts/run_search_benchmark.py
    uv run scripts/run_search_benchmark.py --top-k 50 --limit-queries 5

Outputs: scripts/benchmark_out/results_<ts>.json  and  summary_<ts>.csv
READ-ONLY: never writes to Firestore.
"""

import argparse
import ast
import csv
import json
import os
import time
from pathlib import Path

import firebase_admin
import numpy as np
from benchmark_queries import QUERIES
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings


BACKEND = Path(__file__).resolve().parents[1]

EMBEDDINGS_COLLECTION = "schemes_embeddings"
KS = [1, 3, 5, 10]
VEC_WEIGHT, BM25_WEIGHT = 0.7, 0.3  # matches searchModelManager.rank()
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
        raise RuntimeError(f"Retrieval benchmark must use {PROD_PROJECT_ID}")


# ----------------------------------------------------------------------------- prod client
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
    app = firebase_admin.initialize_app(cred, name="prod_bench")
    return firestore.client(app)


def embedder():
    return AzureOpenAIEmbeddings(
        azure_endpoint=require_env("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
        api_key=require_env("AZURE_OPENAI_EMBEDDING_API_KEY"),
        api_version=require_env("OPENAI_EMBEDDING_API_VERSION"),
        model=require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        dimensions=2048,
    )


# ----------------------------------------------------------------------------- corpus
def load_scheme_meta(db):
    """Read only the scheme fields used by retrieval and evaluation."""
    meta = {}
    for d in db.collection("schemes").stream():
        data = d.to_dict()
        st = data.get("scheme_type")
        if isinstance(st, str):
            try:
                st = ast.literal_eval(st)
            except Exception:
                st = [st]
        cats = {c.strip() for c in st} if isinstance(st, list) else set()
        meta[d.id] = {
            "scheme": data.get("scheme", ""),
            "categories": cats,
            "search_booster": data.get("search_booster", "") or "",
        }
    return meta


# ----------------------------------------------------------------------------- search path (mirrors SearchModel)
def run_search(db, emb, meta, query_text, top_k):
    """Return ranked IDs from the legacy REST production search path."""
    vec = emb.embed_query(query_text)
    vq = (
        db.collection(EMBEDDINGS_COLLECTION)
        .find_nearest(
            vector_field="embedding",
            query_vector=Vector(vec),
            distance_measure=DistanceMeasure.COSINE,
            limit=top_k,
        )
        .get()
    )
    ids = [d.id for d in vq]
    if not ids:
        return []

    # linear-decay vec score, then min-max normalise (exactly as searchModelManager.search)
    vec_scores = [(top_k - i) / top_k for i in range(len(ids))]
    if len(vec_scores) > 1 and max(vec_scores) > min(vec_scores):
        lo, hi = min(vec_scores), max(vec_scores)
        vec_scores = [(s - lo) / (hi - lo) for s in vec_scores]
    vec_map = dict(zip(ids, vec_scores))

    # BM25 over search_booster of the retrieved candidates (exactly as .rank)
    docs = [Document(page_content=meta.get(i, {}).get("search_booster", ""), metadata={"id": i}) for i in ids]
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = len(docs)
    ranked = retriever.invoke(query_text)
    bm25_map = {doc.metadata["id"]: 1.0 - (n / retriever.k) for n, doc in enumerate(ranked)}

    combined = [(i, VEC_WEIGHT * vec_map[i] + BM25_WEIGHT * bm25_map.get(i, 0.0)) for i in ids]
    combined.sort(key=lambda x: x[1], reverse=True)
    return [i for i, _ in combined]


# ----------------------------------------------------------------------------- metrics
def eval_binary(ranked_ids, relevant_ids, ks):
    """Binary relevance, set-based (order within the top K is ignored).

    P@K  = of the top K results, fraction that are relevant  ("are the results good?")
    R@K  = of all relevant schemes, fraction captured in top K ("did we find them all?")
    """
    rel = [1 if i in relevant_ids else 0 for i in ranked_ids]
    total_rel = len(relevant_ids)
    out = {}
    for k in ks:
        hits = sum(rel[:k])
        out[f"P@{k}"] = hits / k
        out[f"R@{k}"] = hits / total_rel if total_rel else 0.0
    return out


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=100, help="candidates pulled from vector search (prod default 100)")
    ap.add_argument("--limit-queries", type=int, default=None, help="only run first N queries (debug)")
    args = ap.parse_args()
    load_prod_environment()

    queries = QUERIES[: args.limit_queries] if args.limit_queries else QUERIES
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = Path(__file__).resolve().parent / "benchmark_out"
    outdir.mkdir(exist_ok=True)

    print(f"Connecting to prod ({os.getenv('FB_PROJECT_ID')}) [READ-ONLY] ...")
    db = prod_db()
    emb = embedder()
    print("Loading scheme metadata (categories, search_booster) ...")
    meta = load_scheme_meta(db)
    print(f"  {len(meta)} schemes loaded.\n")

    def pool_relevant(q):
        """Category-pool relevance (secondary, weak/contaminated signal)."""
        cats = set(q["pool_categories"])
        if q.get("pool_mode") == "and":
            return {sid for sid, m in meta.items() if cats <= m["categories"]}
        return {sid for sid, m in meta.items() if cats & m["categories"]}

    per_query = []
    for q in queries:
        gold = set(q.get("gold_relevant", []))
        pool = pool_relevant(q)
        ranked = run_search(db, emb, meta, q["query"], args.top_k)
        row = {
            "id": q["id"],
            "query": q["query"],
            "tier": q["tier"],
            "n_gold": len(gold),
            "n_pool": len(pool),
            # PRIMARY: human-judged gold (uncontaminated). Only for queries that have a gold set.
            "gold": eval_binary(ranked, gold, KS) if gold else None,
            # SECONDARY: category pool (weak signal, reported for context).
            "pool": eval_binary(ranked, pool, KS),
        }
        per_query.append(row)
        top = ranked[0] if ranked else None
        g = row["gold"]
        gold_str = f"GOLD P@5={g['P@5']:.2f} R@5={g['R@5']:.2f} R@10={g['R@10']:.2f}" if g else "GOLD  —  (generic)"
        print(
            f"[{q['tier']:<8}] {q['id']}  {gold_str} | pool P@5={row['pool']['P@5']:.2f} "
            f"| gold={len(gold):2d} pool={len(pool):3d} | top: {meta.get(top, {}).get('scheme', '-')[:38]}"
        )

    # ---- aggregate (macro-average over a subset of queries)
    def agg(rows, key, metric):
        vals = [pq[key][metric] for pq in rows if pq.get(key)]
        return float(np.mean(vals)) if vals else 0.0

    def block(title, rows, key):
        print("\n" + "=" * 64)
        print(title)
        print("=" * 64)
        if not any(pq.get(key) for pq in rows):
            print("  (no queries with this ground truth)")
            return {}
        print(f"{'metric':<12}" + "".join(f"K={k:<7}" for k in KS))
        for name, m in [("Precision", "P@"), ("Recall", "R@")]:
            print(f"{name:<12}" + "".join(f"{agg(rows, key, f'{m}{k}'):<9.3f}" for k in KS))
        out = {}
        for k in KS:
            out[f"P@{k}"] = agg(rows, key, f"P@{k}")
            out[f"R@{k}"] = agg(rows, key, f"R@{k}")
        return out

    specific = [pq for pq in per_query if pq["tier"] == "specific"]

    # ---- per-query GOLD breakdown + average row (specific queries) ----
    print("\n" + "=" * 78)
    print("PER-QUERY BREAKDOWN — GOLD (specific queries), with AVERAGE")
    print("=" * 78)
    hdr = f"{'id':<5}{'query':<44}" + "".join(f"P@{k:<4}R@{k:<4}" for k in KS)
    print(hdr)
    print("-" * len(hdr))
    for pq in specific:
        g = pq["gold"]
        cells = "".join(f"{g[f'P@{k}']:<5.2f}{g[f'R@{k}']:<5.2f}" for k in KS)
        print(f"{pq['id']:<5}{pq['query'][:43]:<44}{cells}")
    print("-" * len(hdr))
    avg_cells = "".join(f"{agg(specific, 'gold', f'P@{k}'):<5.2f}{agg(specific, 'gold', f'R@{k}'):<5.2f}" for k in KS)
    print(f"{'AVG':<5}{'(macro-average over specific queries)':<44}{avg_cells}")

    summary = {}
    summary["gold_specific"] = block(
        "PRIMARY — GOLD ground truth, human-judged (specific queries only)\n"
        "         uncontaminated; judge search quality by these numbers",
        specific,
        "gold",
    )
    summary["pool_specific"] = block(
        "SECONDARY — category-pool (specific queries)  [weak signal: scheme_type\n"
        "            is embedded, so this is partly circular — context only]",
        specific,
        "pool",
    )
    summary["pool_generic"] = block(
        "FLOOR — category-pool (generic chip queries)  [broad by design; a high\n"
        "        score here is expected and not evidence of quality]",
        [pq for pq in per_query if pq["tier"] == "generic"],
        "pool",
    )

    # ---- write artifacts
    (outdir / f"results_{ts}.json").write_text(
        json.dumps(
            {"config": vars(args), "ks": KS, "weights": [VEC_WEIGHT, BM25_WEIGHT], "per_query": per_query, "summary": summary},
            indent=2,
        )
    )
    with open(outdir / f"summary_{ts}.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["block", "metric", "value"])
        for block_name, metrics in summary.items():
            for k, v in metrics.items():
                w.writerow([block_name, k, f"{v:.4f}"])

    print(f"\nWrote:\n  {outdir / f'results_{ts}.json'}\n  {outdir / f'summary_{ts}.csv'}")


if __name__ == "__main__":
    main()
