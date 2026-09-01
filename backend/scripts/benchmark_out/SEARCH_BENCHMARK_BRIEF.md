# Search Quality Benchmark — Brief

_SchemesSG v3 · prod corpus (684 schemes) · read-only · 2026-07-19_

## What we are looking at

We measured how good the scheme search is at returning the *right* schemes for a
user's query. Because there was no labelled "correct answers" dataset, we built one:

- **Queries** — the actual prompts the product invites users to type, taken verbatim
  from the frontend (the search placeholder, the two example hints, and the category
  chips). We split them into **specific** (real compound phrasings like _"healthcare
  subsidies for seniors"_) and **generic** (the broad _"I need X support"_ chips).
- **Ground truth ("gold")** — for each specific query, a hand-picked set of schemes
  that a caseworker would consider genuinely relevant, judged by reading each scheme's
  **full description and "who is it for" field** — not its category tag. (The category
  tag is baked into the text the search embeds, so scoring against it would be circular.)

We then ran **two versions of the search** against the **same corpus and the same gold
set**, so any difference reflects the search itself, not the data:

| Version | Embedding model | Index | Ranking |
|---|---|---|---|
| **Legacy** (pre-Aug 2025) | local `all-mpnet` (768-dim) | FAISS | vector similarity only |
| **Current** | Azure `text-embedding-3-large` (2048-dim) | Firestore vector search | hybrid: 70% vector + 30% BM25 keyword |

> Note: the legacy model was re-run on **today's** 684 schemes (not its original
> smaller corpus), specifically so the comparison is apples-to-apples.

## What the table represents

Each row is a metric; each column is a **cut-off K** — "if we look only at the top K
results, how good are they?" We report K = 1, 3, 5, 10 (users scan the first handful).

| Version | P@1 | P@3 | P@5 | P@10 | R@5 | R@10 |
|---|---|---|---|---|---|---|
| **Legacy** (mpnet + FAISS, vector-only) | 0.50 | 0.72 | 0.67 | 0.47 | 0.28 | 0.40 |
| **Current** (Azure + Firestore + hybrid) | **1.00** | **0.94** | **0.83** | **0.83** | **0.36** | **0.72** |
| **Change** | +0.50 | +0.22 | +0.16 | +0.36 | +0.08 | +0.32 |

_Numbers are macro-averaged over the six specific queries. Order within the top K is
ignored — this is a set-retrieval task (the user wants to see the set of helpful
schemes, not navigate to one answer)._

### Per-query breakdown (Current vs Legacy)

Where the aggregate gains come from — P@5 (top-5 quality) and R@10 (coverage) per query:

| Query | Legacy P@5 | Current P@5 | Legacy R@10 | Current R@10 |
|---|---|---|---|---|
| s01 — single parent + financial aid | 0.20 | **0.80** | 0.10 | **0.70** |
| s02 — healthcare subsidies for seniors | 0.60 | 0.60 | 0.62 | **0.75** |
| s03 — education grants for low-income | 0.60 | 0.60 | 0.36 | **0.64** |
| s04 — seniors or caregivers | 1.00 | 1.00 | 0.33 | **0.67** |
| s05 — disability or transport | 0.80 | **1.00** | 0.38 | **0.77** |
| s06 — legal or safety | 0.80 | **1.00** | 0.62 | **0.77** |
| **Average** | **0.67** | **0.83** | **0.40** | **0.72** |

_(P@1 not shown per-query for brevity; at the aggregate level it rose 0.50 → 1.00 —
legacy put a wrong result at the #1 slot for s02, s03 and s05, all of which Current
gets right.)_

## What Precision@K and Recall@K mean

Both answer a different half of "was the search good?"

- **Precision@K — "of what I showed you, how much was useful?"**
  Of the top K results, the fraction that are genuinely relevant.
  P@5 = 0.83 → about **4 of every 5** results in the top 5 are on-target.
  This is the metric a user *feels* — a page full of relevant results.

- **Recall@K — "of everything useful, how much did I find?"**
  Of *all* the relevant schemes that exist for the query, the fraction that showed
  up in the top K. R@10 = 0.72 → the top 10 surfaces **~72% of the known-good schemes**.
  This is the metric that matters for coverage — not missing help the user qualifies for.

There is a natural tension: cast a wider net (bigger K) and you catch more good ones
(recall up) but dilute with weaker ones (precision down). Both being high is the goal.

> **Reading recall correctly:** our gold sets hold 8–15 schemes, so Recall@5 can never
> exceed 5 ÷ gold-size. Treat **R@10 as the meaningful recall number**; R@1/R@3/R@5 are
> capped low by construction, not by search quality.

## Interesting insights from the improvement

**1. The top result went from a coin-flip to always-right.**
P@1 rose **0.50 → 1.00**. The legacy model put a non-relevant scheme in the #1 slot for
half the queries (healthcare-for-seniors, education-grants, disability-support all had a
wrong top result). The current search leads with a genuinely relevant scheme every time.
This is the single most visible win — the first thing a user sees is now reliably useful.

**2. Coverage nearly doubled.**
R@10 rose **0.40 → 0.72**. The legacy model tended to find one or two good matches and
then drift; the current stack pulls in most of the relevant set within ten results.
Concretely on _"single parent + financial aid"_: legacy found one good scheme and
nothing more (P@10 = 0.10), while current holds P@10 = 0.70 — it keeps finding relevant
help instead of stalling.

**3. Legacy quality *decayed* deeper into the list; current stays strong.**
Legacy P@10 (0.47) is *lower* than its P@3 (0.72) — results got worse the further you
scrolled. Current holds P@3 = 0.94 and P@10 = 0.83 — the whole first page stays relevant.
A user who scrolls is rewarded, not punished.

**4. The gains are concentrated on nuanced, compound queries.**
Simpler queries with a strong keyword (_legal_, _caregivers_) were already decent on the
legacy stack. The big jumps came on queries needing the engine to honour a **qualifier** —
_seniors_ **healthcare** subsidies, **low-income** education grants, **disability**
transport. The richer Azure embeddings plus BM25 keyword grounding handle "the specific
thing within the broad topic" far better.

**5. One honest weak spot remains.**
_"Healthcare subsidies for seniors"_ still scores P@5 = 0.60 on the current stack: it
correctly leads with Pioneer/Merdeka/CHAS but then mixes in senior-related schemes that
aren't healthcare *subsidies* (a digital-access grant, a housing bonus). If any tuning is
done next, this "right topic, wrong sub-type" case is where to focus.

## Caveats (so the numbers aren't over-read)

- The improvement bundles **two** changes — the embedding model *and* the added BM25
  reranking. It shows the net gain of "old search → new search," not which change did
  what. (An ablation could separate them.)
- Ground truth is **one annotator's** judgment over **six** specific queries. Directionally
  strong and consistent, but widen the query set and add a second labeller for tighter
  confidence.
- Metrics are set-based (order within the top K ignored), matching the product's goal of
  surfacing a *set* of options rather than one ranked answer.
