# Search and Agent Quality Benchmarks

Measures SchemesSG search **retrieval quality** (did the right schemes come back)
and agent quality (did the agent call the right tools and produce a grounded,
relevant answer).

## Run

`run_search_benchmark.py` reads production Firestore without writing to it:

```bash
cd backend
uv run scripts/run_search_benchmark.py                    # all queries
uv run scripts/run_search_benchmark.py --top-k 50         # smaller candidate pool
uv run scripts/run_search_benchmark.py --limit-queries 6  # specific queries only
```

Reads `functions/.env.prod` (Firebase + Azure embedding creds). Never writes to Firestore.

Re-run the legacy FAISS comparator when refreshing the A/B results:

```bash
uv run --with "numpy<2" --with torch --with transformers --with faiss-cpu \
  scripts/run_search_benchmark_legacy.py
```

The agent evaluation runs in two phases. Phase 1 reads the production scheme
corpus but replaces all agent persistence with an in-memory evaluation store:

```bash
cd backend/functions
uv run ../scripts/run_agent_eval.py
uv run --with "numpy<2" --with "ragas==0.2.15" \
  --with "langchain-community==0.3.1" --with langchain-openai \
  ../scripts/score_ragas_from_traces.py ../scripts/benchmark_out/agent_traces_TIMESTAMP.json
```

## Where results are saved

All generated artifacts are saved under
`backend/scripts/benchmark_out/` from the repository root:

| File | Contents |
|---|---|
| `results_<ts>.json` | Per-query precision/recall metrics and relevance-set sizes |
| `summary_<ts>.csv` | Aggregate retrieval metrics |
| `legacy_summary_<ts>.csv` | Legacy-search comparison metrics |
| `agent_traces_<ts>.json` | Agent messages, tool calls, tool outputs, and RAGAS samples |
| `agent_tooluse_summary_<ts>.csv` | Deterministic tool-use metrics |
| `agent_eval_report_<ts>.json/.csv` | Combined tool-use, faithfulness, and response-relevancy report |
| `SEARCH_BENCHMARK_BRIEF.md` | Human-readable retrieval findings |

Raw timestamped artifacts remain local and are gitignored because traces can contain
production-derived scheme records. The committed `SEARCH_BENCHMARK_BRIEF.md`
preserves the reviewed retrieval baseline.

The agent harness does not write checkpoints, `llmQuery` documents, or rerank
documents to production Firestore.

The retrieval runner mirrors the legacy REST search path in
`functions/ml_logic/searchModelManager.py`. Agent-search quality is evaluated
end to end by `run_agent_eval.py`; it is not measured by the legacy retrieval runner.

## File map

| File | Purpose |
|---|---|
| `benchmark_queries.py` | Curated retrieval queries and relevance sets |
| `run_search_benchmark.py` | Current REST retrieval benchmark |
| `run_search_benchmark_legacy.py` | Historical FAISS comparator used by the A/B table |
| `agent_eval_queries.py` | Agent tool-use and response test cases |
| `run_agent_eval.py` | Phase 1: run the agent and save in-memory-backed traces |
| `score_ragas_from_traces.py` | Phase 2: score faithfulness and response relevancy |
| `benchmark_out/SEARCH_BENCHMARK_BRIEF.md` | Reviewed baseline results safe to commit |

## What it measures

Reproduces the exact production search path from `ml_logic/searchModelManager.py`:

```
query -> Azure text-embedding-3-large (2048d)
      -> Firestore find_nearest (COSINE) on schemes_embeddings, limit=top_k
      -> BM25 rerank on search_booster
      -> combined = 0.7 * vec_norm + 0.3 * bm25
```

**Metrics** (macro-averaged) at **K = 1, 3, 5, 10** — set-based, order within the top K ignored:

| Metric | Question it answers |
|---|---|
| **Precision@K** | Of the top K results, what fraction are relevant? ("are the results good?") |
| **Recall@K** | Of all relevant schemes, what fraction landed in the top K? ("did we find them all?") |

MAP and MRR were dropped: both are rank metrics (MAP scores ordering within the top K;
MRR scores only the rank of the first hit). This is a set-retrieval task — the user wants
to *see the set* of schemes that could help, not navigate to one correct answer — so
ordering is not a goal, and MRR was saturated at 1.00 (uninformative) anyway.

## Ground-truth curation (v2) — read this before trusting a number

The queries are the **actual product-invited prompts**, taken verbatim from the
frontend (`frontend/src/lib/landing-i18n/translations/en.ts`): the search
placeholder, the two hint examples, and the ten category chips. Two tiers:

- **specific** — real compound phrasings ("healthcare subsidies for seniors",
  "single parent looking for financial assistance"). These are the discriminating tests.
- **generic** — the "I need X support" chips. Broad by design; a floor, not a test.

Each specific query carries **two** relevance signals, reported separately:

### PRIMARY — GOLD (human-judged, uncontaminated) — trust these numbers

`gold_relevant` is a hand-picked set of scheme_ids judged genuinely on-target for
the query **from each scheme's description, not its category tag**.

Why "not the category tag" matters — the circularity trap:
`scheme_type` is **concatenated into the text that gets embedded**
(`scripts/populate_embeddings.py::build_desc_booster` includes `scheme_type`). So
"a scheme is relevant iff it carries category X" is *partly circular* — you're
asking the embedding to find schemes whose embedded text literally contains X.
That inflates precision. The gold set is judged independently of both the tag and
the ranking, so metrics over it are honest. It is small and precise on purpose.

### SECONDARY — category pool (weak signal, context only)

`pool_categories` + `pool_mode` ("and"/"or"). Reported but **flagged as partly
circular** (see above) and, for broad categories, non-discriminating. Use only to
sanity-check recall scale. Do not quote as a quality result.

### Why gold beats the old category-only method

The first version scored P@5 ≈ 0.94 using category-match relevance — but that was
inflated by (a) circularity and (b) categories so broad (~40% of the corpus) that
precision was nearly free. The committed gold baseline scores P@5 = 0.83 and, more usefully,
**localises the failures** (e.g. single-parent-specific schemes ranked far below
generic financial aid). A benchmark that says "94%, all good" is less useful than
one that identifies the specific queries that remain weak.

### On Recall

Even against gold, Recall@K is bounded by the gold-set size vs K (gold sets hold
8-15 schemes, so R@5 cannot exceed 5/gold-size). Read R@K as "how much of the
known-good set surfaced by K"; **R@10 is the meaningful recall number**. Judge
overall quality by **Precision@K and Recall@10 on the GOLD block**.

## Extending / maintaining

- **Add a query**: append to `QUERIES` in `benchmark_queries.py`. For a real test,
  set `tier: "specific"`, write `intent`, and hand-pick `gold_relevant` ids
  (label from descriptions). scheme_ids must exist in prod.
- **Re-label after data refresh**: gold ids are pinned to specific schemes; if the
  corpus changes materially, re-verify them.
- **Compare configs**: change `VEC_WEIGHT`/`BM25_WEIGHT` or `--top-k`, re-run, diff
  the GOLD block across CSVs.
