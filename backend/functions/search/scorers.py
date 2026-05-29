import pandas as pd
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


VEC_SIMILARITY_WEIGHT = 0.7
BM25_SIMILARITY_WEIGHT = 0.3


def rank_results(query_text: str, results: pd.DataFrame) -> pd.DataFrame:
    """Re-rank results using BM25 and combine with vector scores.

    Returns a DataFrame with 'bm25_score' and 'combined_scores' columns, sorted
    by combined score descending.
    """
    docs = [
        Document(page_content=content or "", metadata={"id": sid})
        for sid, content in zip(results["scheme_id"], results["search_booster"])
    ]
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = len(docs)

    bm25_results = [
        (doc.metadata["id"], 1.0 - (i / retriever.k)) for i, doc in enumerate(retriever.invoke(query_text))
    ]
    bm25_df = pd.DataFrame(bm25_results, columns=["scheme_id", "bm25_score"])

    results = pd.merge(results, bm25_df, on="scheme_id", how="left")
    results["combined_scores"] = (
        results["vec_similarity_score"] * VEC_SIMILARITY_WEIGHT
        + results["bm25_score"].fillna(0) * BM25_SIMILARITY_WEIGHT
    )
    return results.sort_values("combined_scores", ascending=False)


def compute_vec_scores(ids: list[str], top_k: int) -> pd.DataFrame:
    """Compute normalized vector similarity scores for a list of ids.

    The scoring uses a linear decay based on position in the results returned
    by the vector search (assumed sorted by similarity). Returns a DataFrame
    with columns `scheme_id` and `vec_similarity_score`.
    """
    if not ids:
        return pd.DataFrame(columns=["scheme_id", "vec_similarity_score"])

    vec_scores = [(top_k - i) / top_k for i in range(len(ids))]

    # Normalize scores to 0-1 range
    if len(vec_scores) > 1 and max(vec_scores) > min(vec_scores):
        vec_scores = [(s - min(vec_scores)) / (max(vec_scores) - min(vec_scores)) for s in vec_scores]

    return pd.DataFrame(zip(ids, vec_scores), columns=["scheme_id", "vec_similarity_score"])
