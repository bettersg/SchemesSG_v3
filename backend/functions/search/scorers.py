import re

import pandas as pd
from rank_bm25 import BM25Okapi


RRF_K = 60
TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


def _rank_desc(scores: list[float]) -> list[float]:
    return pd.Series(scores).fillna(0).rank(method="min", ascending=False).tolist()


def _normalize_bm25_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []

    scores = [max(0.0, score) for score in scores]
    max_score = max(scores)
    if max_score == 0:
        return [0.0 for _ in scores]

    return [score / max_score for score in scores]


def _normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0 for _ in scores]

    return [(score - min_score) / (max_score - min_score) for score in scores]


def rank_results(query_text: str, results: pd.DataFrame) -> pd.DataFrame:
    """Re-rank results using BM25 and fuse with vector rank using RRF.

    Returns a DataFrame with 'bm25_score' and 'combined_scores' columns, sorted
    by combined score descending.
    """
    results = results.copy()
    results["bm25_score"] = compute_bm25_scores(
        query_text,
        [content or "" for content in results["search_booster"]],
    )
    results["combined_scores"] = compute_rrf_scores(
        results["vec_similarity_score"].tolist(),
        results["bm25_score"].fillna(0).tolist(),
    )
    return results.sort_values("combined_scores", ascending=False)


def compute_bm25_scores(query_text: str, documents: list[str]) -> list[float]:
    """Compute normalized BM25 relevance scores for a candidate set."""
    query_tokens = _tokenize(query_text)
    corpus = [_tokenize(document) for document in documents]

    if not query_tokens or not corpus or not any(corpus):
        return [0.0 for _ in documents]

    raw_scores = BM25Okapi(corpus).get_scores(query_tokens)
    return _normalize_bm25_scores([float(score) for score in raw_scores])


def compute_rrf_scores(vec_scores: list[float], bm25_scores: list[float]) -> list[float]:
    """Fuse vector and BM25 rankings using Reciprocal Rank Fusion."""
    if not vec_scores:
        return []

    vec_ranks = _rank_desc(vec_scores)
    bm25_ranks = _rank_desc(bm25_scores)
    raw_scores = [
        (1 / (RRF_K + vec_rank)) + (1 / (RRF_K + bm25_rank)) for vec_rank, bm25_rank in zip(vec_ranks, bm25_ranks)
    ]
    return _normalize_scores(raw_scores)


def compute_vec_scores(ids: list[str], distances: list[float]) -> pd.DataFrame:
    """Convert real cosine distances into a normalized 0-1 relevance score.

    Firestore returns a cosine distance per match where 0 means identical and
    larger means less similar. We turn that into a relevance score where a
    closer match scores higher. Returns a DataFrame with columns `scheme_id` and
    `vec_similarity_score`.
    """
    if not ids:
        return pd.DataFrame(columns=["scheme_id", "vec_similarity_score"])

    # Smaller distance = better match = higher relevance.
    relevance = [-d for d in distances]

    # Normalize to 0-1 across this result set (best match -> 1).
    if len(relevance) > 1 and max(relevance) > min(relevance):
        lo, hi = min(relevance), max(relevance)
        relevance = [(r - lo) / (hi - lo) for r in relevance]
    else:
        relevance = [1.0 for _ in relevance]

    return pd.DataFrame(zip(ids, relevance), columns=["scheme_id", "vec_similarity_score"])
