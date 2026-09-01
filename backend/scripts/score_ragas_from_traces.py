"""Phase 2 of the agent eval — score RAGAS faithfulness + response relevancy from
agent traces dumped by run_agent_eval.py.

Runs in an ISOLATED env with pinned ragas/langchain (which conflict with the agent's
modern langchain, hence the two-phase split). Reads the traces JSON, scores the two
LLM-judge dimensions, merges the tool-use summary back in, and writes the final report.

  DIMENSION 2 — Faithfulness: is the answer grounded in the tool outputs (contexts)?
                Low score => the agent invented facts not supported by what tools returned.
  DIMENSION 3 — Response Relevancy: does the answer actually address the user's query?

Scope: both RAGAS metrics assume a retrieval-grounded answer, so we score them only on
turns that actually retrieve scheme facts (kind == "search", plus the retrieve/apply
agent turns). Pure-generation turns (email drafting, "is there anything new" web probes)
have no factual context to be faithful to and produce a bulleted list that RAGAS's
reverse-question relevancy step mis-scores — including them would unfairly drag the mean.
Those turns are still fully covered by Dimension 1 (tool-use accuracy).

Run (from backend/functions, pins matter — see run_agent_eval.py header):
    uv run --with "numpy<2" --with "ragas==0.2.15" --with "langchain-community==0.3.1" \
        --with langchain-openai ../scripts/score_ragas_from_traces.py <traces.json>

Reads .env.dev for the judge LLM + embeddings.
"""

import csv
import json
import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


FUNCTIONS_DIR = Path(__file__).resolve().parents[1] / "functions"
load_dotenv(FUNCTIONS_DIR / ".env.dev", override=True)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: score_ragas_from_traces.py <agent_traces_*.json>")
    traces_path = Path(sys.argv[1])
    data = json.loads(traces_path.read_text())
    all_samples = data["ragas_samples"]
    rows = data.get("per_query", [])
    tool_summary = data.get("tool_use_summary", {})

    # Score only retrieval-grounded turns; strip helper keys RAGAS doesn't accept.
    scorable = [s for s in all_samples if s.get("ragas_scorable")]
    scorable_ids = [s["id"] for s in scorable]
    samples = [{k: s[k] for k in ("user_input", "response", "retrieved_contexts")} for s in scorable]
    print(f"RAGAS scored on {len(samples)}/{len(all_samples)} retrieval-grounded turns: {scorable_ids}")
    print("(email-drafting / web-probe turns excluded — no factual context to ground; "
          "still covered by tool-use accuracy.)")

    from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, ResponseRelevancy

    # Judge = the same chat model family the agent uses (gpt-5.4-mini, SEA region).
    judge = LangchainLLMWrapper(
        AzureChatOpenAI(
            azure_endpoint=require_env("AZURE_OPENAI_ENDPOINT_SEA"),
            api_key=require_env("AZURE_OPENAI_API_KEY_SEA"),
            api_version=require_env("OPENAI_API_VERSION"),
            azure_deployment="gpt-5.4-mini",
            temperature=0,
        )
    )
    emb = LangchainEmbeddingsWrapper(
        AzureOpenAIEmbeddings(
            azure_endpoint=require_env("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
            api_key=require_env("AZURE_OPENAI_EMBEDDING_API_KEY"),
            api_version=require_env("OPENAI_EMBEDDING_API_VERSION"),
            model=require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            dimensions=2048,
        )
    )

    # RAGAS requires at least one non-empty context per sample.
    for s in samples:
        if not s.get("retrieved_contexts"):
            s["retrieved_contexts"] = ["(no tool output for this turn)"]

    ds = EvaluationDataset.from_list(samples)
    res = evaluate(dataset=ds, metrics=[Faithfulness(llm=judge), ResponseRelevancy(llm=judge, embeddings=emb)])
    df = res.to_pandas()

    def metric_column(*names):
        for n in names:
            if n in df.columns:
                return df[n]
        return None

    faith = metric_column("faithfulness")
    rel = metric_column("answer_relevancy", "response_relevancy")

    def mean(series):
        if series is None:
            return None
        vals = [float(v) for v in series if v is not None and not (isinstance(v, float) and math.isnan(v))]
        return sum(vals) / len(vals) if vals else None

    print("\n" + "=" * 68)
    print("AGENT EVAL — full report")
    print("=" * 68)
    print("\nDIMENSION 1 — TOOL-USE ACCURACY (deterministic)")
    for k in ("tool_precision", "tool_recall", "tool_f1", "tool_exact_match"):
        if k in tool_summary:
            print(f"  {k:<18}: {float(tool_summary[k]):.3f}")

    print("\nDIMENSIONS 2+3 — RAGAS (LLM-judge)")
    print(f"  faithfulness      : {mean(faith):.3f}  (answer grounded in tool outputs — no hallucination)")
    print(f"  response_relevancy: {mean(rel):.3f}  (answer addresses the user query)")

    # map RAGAS scores back to query ids (df rows are in scorable_ids order)
    faith_by_id = {scorable_ids[i]: float(faith.iloc[i]) for i in range(len(df))} if faith is not None else {}
    rel_by_id = {scorable_ids[i]: float(rel.iloc[i]) for i in range(len(df))} if rel is not None else {}

    print("\nPer-query  (— = not RAGAS-scorable, tool-use only):")
    print(f"  {'id':<5}{'kind':<7}{'toolF1':<8}{'faith':<8}{'relevancy':<10}")
    for r in rows:
        fv = faith_by_id.get(r["id"])
        rv = rel_by_id.get(r["id"])
        fs = f"{fv:<8.2f}" if fv is not None else f"{'—':<8}"
        rs = f"{rv:<10.2f}" if rv is not None else f"{'—':<10}"
        print(f"  {r['id']:<5}{r.get('kind',''):<7}{r['tool_use']['f1']:<8.2f}{fs}{rs}")
        if r.get("ragas_scorable"):
            r["ragas"] = {"faithfulness": fv, "response_relevancy": rv}

    # ---- write merged final report
    summary = dict(tool_summary)
    summary["faithfulness"] = mean(faith)
    summary["response_relevancy"] = mean(rel)
    out = traces_path.with_name(traces_path.name.replace("agent_traces_", "agent_eval_report_"))
    out.write_text(json.dumps({"summary": summary, "per_query": rows}, indent=2, default=str))
    csv_out = out.with_suffix(".csv")
    with open(csv_out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["metric", "value"])
        for k, v in summary.items():
            w.writerow([k, f"{v:.4f}" if isinstance(v, float) else v])
    print(f"\nWrote:\n  {out}\n  {csv_out}")


if __name__ == "__main__":
    main()
