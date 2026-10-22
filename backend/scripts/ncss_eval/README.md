# NCSS taxonomy extraction eval (issue #406, Phase 1 — local only)

Offline harness. Not deployed. Own uv env (`uv run python ...` in this dir). Secrets from `../../scheme-processor/.env`
(AZURE_OPENAI_*; deployment `gpt-6-luna`). Prod pulls are READ-ONLY and save only subsets to `data/` (gitignored).

## Files
- `taxonomy.py` — vocab v2 (who 46 / what 55 / scheme_type 36), definitions, NCSS parents, `age_terms()`, `SCHEME_CATEGORY_MAPPING_V2`.
- `common.py` — `frozen_state()` = the ONE text every arm/labeller/reviewer sees.
- `run_luna.py <effort>` — strict json_schema + enums + caps. `SAMPLE=<jsonl> RUN_TAG=-x` for other sets. Output `data/runs/luna-<effort><tag>/`.
- `score.py [--split dev|test|all]` — P/R/F1 per field (+ age vs profile split), rule checks, exclusions. `errors.py <field> [split]` — FP/FN by term.
- `score_suite.py -suite` — disability vs mental-health suite (NCSS parent roll-up). `category_coverage.py` — 10-category diff old vs v2.
- `sample_dev.py`, `fetch_carecorner_prod.py`, `fetch_disability_suite.py` — data pulls. `run_jev.py`, `probe_luna.py` — Jev (dropped) / probe.
- `prompt_preview.md` — rendered system prompt (regenerate after prompt/taxonomy edits; see task_plan.md).
- data (untracked): `sample_dev_50.jsonl`, `gold_draft.json` (49, model-drafted, NOT yet user-reviewed), `gold_review.csv`, `split.json`, `probes*.json*`, `disability_suite_*`, `carecorner_prod.jsonl`, `runs*/`.

## Typical loop
`mv data/runs/luna-medium data/runs_vN/…; uv run python run_luna.py medium; uv run python score.py --split dev` (tune on dev only), then `--split test`.
LLM run-to-run noise is about +/-0.02 F1: repeat before trusting small deltas.
