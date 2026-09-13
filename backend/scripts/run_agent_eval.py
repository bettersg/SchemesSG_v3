"""Agent eval harness — evaluates the SchemesSG LangGraph router agent end to end.

Runs the REAL agent (RouterAgentGraph) against production scheme data + Azure
gpt-5.4-mini without persisting evaluation state,
captures the full message trace per query (tool calls + tool outputs + final answer),
and scores THREE dimensions:

  1. TOOL-USE ACCURACY (deterministic, from a curated expected-tools ground truth):
     precision / recall / F1 over the set of tool names called, plus exact-set-match.
     Mirrors RAGAS ToolCallAccuracy but computed transparently against our own labels.

  2. RAGAS FAITHFULNESS (LLM-judge): is the final answer grounded in the tool outputs
     (retrieved contexts), i.e. no hallucinated eligibility/benefit claims?

  3. RAGAS RESPONSE RELEVANCY (LLM-judge): does the answer actually address the query?

Uses the same query IDs as the search benchmark where they overlap (a01-a06), plus
agent-specific queries (a07-a10) that exercise the non-search tools.

TWO-PHASE design (deliberate): the agent needs the project's modern langchain, but
ragas pins an OLD langchain that conflicts with the agent's checkpointer. Running both
in one process breaks. So:

  Phase 1 (this script, project venv) — run the agent, score Tool-Use Accuracy
           (deterministic, no ragas), and DUMP per-query traces to a JSON file.
  Phase 2 (score_ragas_from_traces.py, isolated env) — read that JSON, score
           faithfulness + response relevancy with ragas, and merge back.

Run:
    cd backend/functions
    uv run ../scripts/run_agent_eval.py                 # phase 1 -> writes traces + tool-use
    uv run ../scripts/run_agent_eval.py --limit 2       # smoke
    # then phase 2 (see score_ragas_from_traces.py header for the pinned invocation)

Must run from backend/functions/ (imports the agent package). Reads .env.prod.
Firestore access is read-only: the graph has no checkpointer, and the query/rerank
persistence seams are replaced with an in-memory evaluation store.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from dotenv import load_dotenv


# Run from backend/functions so `agent`, `integrations`, `utils` import cleanly.
FUNCTIONS_DIR = Path(__file__).resolve().parents[1] / "functions"
sys.path.insert(0, str(FUNCTIONS_DIR))
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "True")
PROD_PROJECT_ID = "schemessg"
_EVAL_RESULTS: dict[str, list[dict]] = {}

from agent_eval_queries import AGENT_QUERIES  # noqa: E402


def load_prod_environment() -> None:
    env_file = FUNCTIONS_DIR / ".env.prod"
    if not load_dotenv(env_file, override=True):
        raise RuntimeError(f"Unable to load production environment: {env_file}")
    if os.getenv("FB_PROJECT_ID") != PROD_PROJECT_ID:
        raise RuntimeError(f"Agent evaluation must use {PROD_PROJECT_ID}")


def save_eval_query(_handler, _query: str, _session_id: str, schemes: list[dict]) -> str:
    doc_id = f"eval-{uuid4().hex}"
    _EVAL_RESULTS[doc_id] = schemes
    return doc_id


def retrieve_eval_results(doc_id: str) -> list[dict]:
    return _EVAL_RESULTS.get(doc_id, [])


def save_eval_rerank(_doc_id: str, schemes: list[dict]) -> str:
    doc_id = f"eval-rerank-{uuid4().hex}"
    _EVAL_RESULTS[doc_id] = schemes
    return doc_id


# ------------------------------------------------------------------ run the agent
def run_agent(query: str, thread_id: str) -> dict:
    """Invoke the compiled router graph once; return trace: tools called, tool outputs, answer."""
    import agent.tools.filter_rerank as filter_rerank_module
    from agent.router import RouterAgentGraph
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    from search import QueryHandler

    _EVAL_RESULTS.clear()
    graph = RouterAgentGraph(firestore_client=None).graph
    with (
        patch.object(QueryHandler, "save_llm_query", save_eval_query),
        patch.object(filter_rerank_module, "_retrieve_search_results_by_doc_id", retrieve_eval_results),
        patch.object(filter_rerank_module, "_save_filtered_reranked_schemes", save_eval_rerank),
    ):
        result = graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config={"configurable": {"thread_id": thread_id}},
        )
    messages = result.get("messages", []) if isinstance(result, dict) else []

    tools_called: list[str] = []
    tool_outputs: list[str] = []
    final_answer = ""
    for m in messages:
        # tool calls live on AIMessages
        tcs = getattr(m, "tool_calls", None)
        if isinstance(m, AIMessage) and isinstance(tcs, list):
            for tc in tcs:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    tools_called.append(name)
        # tool outputs (RAGAS contexts) live on ToolMessages
        if isinstance(m, ToolMessage):
            content = m.content if isinstance(m.content, str) else json.dumps(m.content, default=str)
            tool_outputs.append(content[:4000])  # cap per-context size
        # final answer = last AIMessage with text content and no tool calls
        if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
            c = m.content
            if isinstance(c, list):
                c = "\n".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
            if isinstance(c, str) and c.strip():
                final_answer = c.strip()

    return {"tools_called": tools_called, "tool_outputs": tool_outputs, "answer": final_answer}


# ------------------------------------------------------------------ dim 1: tool-use accuracy
def tool_use_scores(called: list[str], expected: set[str], allow_extra: set[str]) -> dict:
    """Set precision/recall/F1 over tool names; 'allow_extra' tools are neither required nor penalised."""
    called_set = set(called)
    # unexpected = called but neither expected nor explicitly allowed
    considered = called_set - allow_extra
    tp = len(considered & expected)
    fp = len(considered - expected)
    fn = len(expected - called_set)
    precision = tp / (tp + fp) if (tp + fp) else (1.0 if not expected else 0.0)
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    exact = expected.issubset(called_set) and not (considered - expected)
    return {"precision": precision, "recall": recall, "f1": f1, "exact_match": 1.0 if exact else 0.0}


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="run only first N queries (smoke test)")
    args = ap.parse_args()
    load_prod_environment()

    queries = AGENT_QUERIES[: args.limit] if args.limit else AGENT_QUERIES
    ts = time.strftime("%Y%m%d-%H%M%S")
    outdir = SCRIPTS_DIR / "benchmark_out"
    outdir.mkdir(exist_ok=True)

    print(f"Running agent ({os.getenv('FB_PROJECT_ID')}) over {len(queries)} queries ...\n")
    rows = []
    ragas_samples = []
    for q in queries:
        try:
            trace = run_agent(q["query"], thread_id=f"eval-{ts}-{q['id']}")
        except Exception as e:
            print(f"{q['id']}  ERROR: {e}")
            continue
        tu = tool_use_scores(trace["tools_called"], q["expected_tools"], q.get("allow_extra", set()))
        # RAGAS faithfulness/relevancy only make sense for retrieval-grounded answers.
        # Scorable iff the query is expected to pull scheme facts (search / retrieve details).
        ragas_scorable = bool(q["expected_tools"] & {"search_schemes", "retrieve_schemes_by_ids"})
        rows.append({"id": q["id"], "kind": q["kind"], "query": q["query"],
                     "expected": sorted(q["expected_tools"]), "called": trace["tools_called"],
                     "tool_use": tu, "ragas_scorable": ragas_scorable})
        ragas_samples.append({
            "user_input": q["query"],
            "response": trace["answer"] or "(no answer produced)",
            "retrieved_contexts": trace["tool_outputs"],
            "id": q["id"],
            "ragas_scorable": ragas_scorable,
        })
        print(f"{q['id']} [{q['kind']:<6}] tools={trace['tools_called']}  "
              f"exp={sorted(q['expected_tools'])}  F1={tu['f1']:.2f} exact={int(tu['exact_match'])}")

    # ---- dim 1 aggregate
    def avg(key):
        vals = [r["tool_use"][key] for r in rows]
        return sum(vals) / len(vals) if vals else 0.0

    print("\n" + "=" * 60)
    print("DIMENSION 1 — TOOL-USE ACCURACY (deterministic)")
    print("=" * 60)
    print(f"  Precision : {avg('precision'):.3f}")
    print(f"  Recall    : {avg('recall'):.3f}")
    print(f"  F1        : {avg('f1'):.3f}")
    print(f"  Exact-set : {avg('exact_match'):.3f}  (fraction of queries with exactly the right tool set)")

    summary = {"tool_precision": avg("precision"), "tool_recall": avg("recall"),
               "tool_f1": avg("f1"), "tool_exact_match": avg("exact_match")}

    # ---- write phase-1 artifacts: tool-use results + traces for phase-2 RAGAS scoring
    traces_path = outdir / f"agent_traces_{ts}.json"
    traces_path.write_text(
        json.dumps({"config": vars(args), "tool_use_summary": summary,
                    "per_query": rows, "ragas_samples": ragas_samples}, indent=2, default=str)
    )
    with open(outdir / f"agent_tooluse_summary_{ts}.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["metric", "value"])
        for k, v in summary.items():
            w.writerow([k, f"{v:.4f}" if isinstance(v, float) else v])

    print(f"\nWrote:\n  {traces_path}\n  {outdir / f'agent_tooluse_summary_{ts}.csv'}")
    print("\nNext — score faithfulness + response relevancy (isolated env):")
    print('  cd backend/functions && uv run --with "numpy<2" --with "ragas==0.2.15" \\')
    print('    --with "langchain-community==0.3.1" --with langchain-openai \\')
    print(f'    ../scripts/score_ragas_from_traces.py "{traces_path}"')


if __name__ == "__main__":
    main()
