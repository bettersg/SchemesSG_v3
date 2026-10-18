# Task Plan — Issue #406: Refine extraction on NCSS taxonomy

Source: issue #406 (decision comment = keep granular terms, split 3 fields on NCSS dimensions). Old plan: task_plan_2026-08-29.md
Inputs (local): ~/Downloads/2026-04-29 Programme Taxonomy V1.0.pptx ; ~/Downloads/Mapping of NCSS & Schemes SG Taxos.xlsx ; extracted text in scratchpad (ncss_dump.txt, mapping_dump.txt)

## DECISIONS + PLAN — 2026-10-18 (Eugene; supersedes gates in CURRENT STATE below; read first)
Inputs: #406 comments 8 Oct (5 Oct NCSS answers) + 14 Oct (needs mapping xlsx `~/Downloads/Mapping NCSS to Schemes SG Taxo_Schemes Type.xlsx`). Model: gpt-6-luna, effort medium (~$0.49/full run; 4-5 runs OK).
Decisions:
- Scope: reclassify ONLY who_is_it_for, what_it_gives, scheme_type (+ parent roll-ups, 10-category mapping) for all ~743 prod schemes (incl. inactive/retired).
- taxonomy.py: apply 5 Oct + 14 Oct as listed in session: parent-only (no rename) Education Support/Healthcare/Employment Support/Financial Planning; merge Mental Health Rehabilitation -> Mental Health; keep Caregiver Support + Housing/Shelter; remove 11 scheme_type terms (+aliases `moved`; COVID/Abuse/Breadwinner = programme re-tag); Legal Aid REMOVED (14 Oct overrides 8 Oct); parent changes (Protection from Violence, Student Care, End-of-Life, General Healthcare Subsidies); provisional=True: Transport, Technology, Community Funding; `Respite care/Caregiver support`->`Respite care`; `Groupwork`->`Group Work`; Homeless parent Persons Experiencing Homelessness; Inmates no parent; Victims of abuse KEPT in who_is_it_for (our proposal, provisional) with Protection from Violence as need; Breadwinner -> Financial & Material Support + text; Fostering NOT own scheme_type; keep Child and Youth Services, Family and Parenting Support, Disability Support, Active Ageing and Social Activities.
- Work in shared checkout on branch feat/406-ncss-taxonomy-eval (user override of worktree rule). Merge origin/stg, resolve conflicts. Do NOT commit unrelated dirty files (helper_scripts/convert_csv_fields_to_arrays.js, GLOSSARY.md, dataset_workflow/).
- No overrides file: NCSS corrections = prompt/taxonomy changes; targeted re-runs on affected schemes + regression sample; one full run at end = signed-off set (frozen results file, keyed by id + input-text hash, gitignored).
- No R6 code translation layer: partner notice + old->new mapping table by email (Eugene sends). Partners get dev API + stg UI for 1 week, parallel to NCSS xlsx review (one row/scheme: old/new tags, parents, changed flag, flagged-first). Eugene manages partner keys.
- GATE: NCSS + partner sign-off before ANY prod write. Prod order: stg->main (code accepts old+new) -> notice -> Firestore backup -> apply frozen results (+classify new/edited only) -> re-embed -> search smoke. Rollback = restore 3 fields from backup. Dev == prod data (sync done).
Today's steps: 1 merge stg + taxonomy edits + regen taxonomy_data.json + tests; 2 harness/disability regression; 3 stg luna env check + push; 4 classify/migrate script (dry run -> dev write, frozen results, diff report); 5 run on dev, re-embed dev, search before/after, category coverage; 6 NCSS xlsx + partner notice/mapping draft. Prod read-only throughout today; confirm before dev Firestore writes.

## CURRENT STATE — end of session 2026-10-04 (read this first when resuming)
Branch feat/406-ncss-taxonomy-eval, PR #449 (open, to stg; description filled in 4 Oct). Head 1911f4be (committed + pushed, includes merge of origin/stg a2e8bd51). Issue #406 status comment posted: issuecomment-5976601928.
DONE: Step 0 renames approved + applied (Seniors family, mental health conditions; migrant domestic workers NOT applied). Round-2 NCSS vocabulary in taxonomy.py. Step 1 code: vendored taxonomy_data.json + helper in both deploy units, separate strict-schema tagger (Azure SDK, effort medium, scheme name passed), fail-closed alias normaliser, Slack/catalog/embedding/frontend compat. Backend suite 345 passed. Two 100-scheme prod samples run (read-only, data/ gitignored); gold review file built.
WAITING:
- USER: review backend/scripts/ncss_eval/data/gold_review_prod.csv (60 rows; vocab in data/vocab_reference.txt) + older gold_review.csv + disability_suite_gold.json. Decide: Learning intervention vs Educational programmes; confirm Child and Youth Services; pregnancy terms keep-both vs merge; reply to NCSS on verbatim searches (privacy/PII check first).
- NCSS: parents Homeless/Inmates/Victims; 7 no-match terms + Educational programmes review; Learning intervention definition; Caregiver Support question; canonical label list; needs draft.
NEXT (me, when gold returns): load corrected_* as gold, rescore luna-medium, tune recall on dev half (prod has Counselling/Emotional care/Info&referral that luna omits: under-tagging or prod over-tagging?), disability/mental-health suite, 3x variance, non-regression on agency/phone/email, gate report -> user sign-off. Regenerate taxonomy_data.json (export_taxonomy.py) after any definition change.
OPEN CODE: partner API translation layer R6 + dated notice (gates stg->main); old-term mentions in firestore_doc.json / benchmark_queries.py / smoke_partner_api.py; set AZURE_OPENAI_TAGGING_DEPLOYMENT on stg + test flow; run frontend vitest (node 'Bad CPU type' locally: run `! cd frontend && npx vitest run src/lib/design-system/categories.test.ts`); migration + re-embed scripts (dry-run only vs local snapshots).
LATER (needs #446 parity, NCSS review, R6): dry-run classify all ~714 active prod schemes + alias coverage; migrate dev then prod with backup; re-embed + before/after search check; drop legacy aliases/old category terms; resolve provisional flags.
HOUSEKEEPING: leaked Azure keys in session output (scheme-processor/.env, gitignored): consider rotating. helper_scripts/convert_csv_fields_to_arrays.js has an unrelated uncommitted change (left alone). Local venvs for ncss_eval and scheme-processor were rebuilt (gitignored); frontend node is broken locally.

## Two-phase structure (user decision)
**PHASE 1 — prompt + taxonomy + evaluation, LOCAL ONLY. No pipeline / Firestore / prod changes.**
**HARD GATE — quality check. Phase 2 does not start until gate passes and user signs off.**
**PHASE 2 — implement in pipeline, all data-processing parts.**

## Fixed decisions
- Keep granular who terms; tag NCSS parent via static table in code (not LLM). Add Adults, Multi-stressed families, Persons with substance and behavioural addictions; add Homeless / Inmates / Victims of abuse as profiles (NCSS itself suggested; Homeless def in xlsx Sheet3). [Q5 decision: adopt NCSS suggestion, mark `provisional`]
- scheme_type KEPT as field, need-domain terms mapped to 21 NCSS needs, pop terms removed. **Keep SCHEME_CATEGORY_MAPPING (10 frontend categories)** -> rebuild it over new need-domain terms so each of 10 categories stays populated.
- Age bands: Children <=12, Youths 13-21, Adults 22-59, Seniors 60+ (applied in code from extracted age).
- Mental health NOT disability (recoverable); PWD = permanent intellectual/physical only.
- Arm A model = gpt-6-luna (effort chosen by eval: compare low vs medium vs high). Arm B = Jev jev-1.13.0 (key in backend/scheme-processor/.env as JEV_API_KEY — gitignored).
- Drop gpt-5 as eval arm (prod baseline measured once for regression context only).

## Advisor-driven rules for Phase 1 (2026-09-29)
- Probe first: 1 call to luna w/ response_format json_schema + reasoning_effort; verify schema-valid output and reasoning-token usage differs by effort. Eval harness calls SDK directly / `drop_params=False` (prod extractor's litellm `drop_params=True` silently drops unsupported params -> fake guarantees).
- Parent model = `{age_group:[...], profile:[...]}` (empty allowed); what_it_gives->intervention parent(s); scheme_type->need parent(s). Store fallback parent for provisional terms (Homeless/Inmates/Victims).
- Ground truth labelled under v2 definitions (NOT prod tags: they contain mental-health-as-disability error). LLM-drafted labels must be user-reviewed. Sample stratified with min positives per term (likely 120-200 schemes); dev/test split; report CIs. NCSS batch-1 likely parent-level only.
- Freeze input text once (same description+eligibility text to both arms). If luna replaces gpt-5 for whole extraction: add non-regression on agency/phone/email/eligibility.
- Gate also covers what_it_gives + scheme_type + 10-category coverage diff (per category: members before vs after, list dropouts).
- Jev: one Noul per granular term (maybe >100 q/scheme) -> read docs.typesafe.ai for batching/pricing/rate limits BEFORE harness design.
- Eval deps in separate dir (e.g. backend/scripts/ncss_eval/ own pyproject), not scheme-processor venv.

## Decisions log (2026-09-29, user)
- Jev DROPPED as classifier (eval: unsuitable). Arm B removed from gate; only luna medium goes to gate.
- luna effort = medium. Age: NCSS bands + granular child terms; tag every overlapping band; ages derived in code.
- Gate criteria now measured on luna-medium only. Remaining Phase 1: user review of gold_review.csv, rescore; per-term FP analysis; prompt iteration; held-out split; edge-case suite (mental health vs disability); category-coverage diff; non-regression on other extracted fields.

## PHASE 1 STATUS (updated 2026-09-29, end of session) — branch feat/406-ncss-taxonomy-eval (pushed). Handoff README: backend/scripts/ncss_eval/README.md
DONE
- Taxonomy v2 in `taxonomy.py` (who 46, what 55, scheme_type 36) w/ NCSS parents, provisional flags, granular child age terms (0-3, 4-6, 7-12, 13-17), age bands derived in code (`age_terms`, overlap rule; open-ended N+ implies Elderly only if seniors targeted; no-restriction => null/null; parent-programmes use children's ages).
- New terms added on user OK: Family and Parenting Support, Disability Support (scheme_type); Active Ageing and Social Activities (scheme_type) + Social and recreational activities (what_it_gives); Child and Youth Services (scheme_type, added by me to rebuild Family & Children — NOT yet user-confirmed).
- Prompt + strict-schema harness (luna, medium effort chosen; Jev DROPPED as unsuitable). Prompt rendered in ncss_prompt_preview.md (repo root, untracked copy) / ncss_eval/prompt_preview.md.
- Advisor review of gold applied; frozen input unified; scorer bugs fixed.
- Disability suite (12 probes + 30 prod): hard violations 0; PWD P1.00 R0.94; MH P0.77 R0.77 (over-tags general counselling; misses multi-audience).
- what_it_gives definitions sharpened (financial-general vs purposeful, educational, emotional care, psychotherapy, employment, referral, social/recreational).
- Category mapping v2 drafted + coverage script.
LATEST NUMBERS (luna-medium, 43-scheme headline set vs UNREVIEWED draft gold): who P.92 R.92 F1 .92 (age terms .95, profile .90); what F1 .83; scheme_type F1 .79 (dropped because gold lacks 'Child and Youth Services' and new terms). dev(19)/test(24) split exists; test who .91, what .81, type .75. Noise +/-0.02.
Category coverage (49 dev schemes, old dev tags+old mapping vs luna scheme_type+v2 mapping) old->new membership: Financial 21->11, Family&Children 20->10, Health 33->20, Housing&Food 7->3, Education 8->2, Employment 8->5, Seniors 21->21, Disability 10->8, Legal 3->4, Community 5->6. Some loss is real (population terms removed), some is old over-tagging. Needs user decision.

PENDING (Phase 1) — user said they will do review later with a new agent
1. USER: review `data/gold_review.csv` (gold labels; start with 6 low-confidence rows; add new terms Child and Youth Services / Active Ageing to gold where they apply). Then rescore on corrected gold.
2. USER: review disability-suite labels `data/disability_suite_gold.json` (blurry: Bizlink Cafe, Tzu Chi, ESP, Project Smile, SAMH Creative Hub).
3. USER: review prompt (ncss_prompt_preview.md) + definitions written by me (Young adults, Persons with special needs, all what_it_gives terms).
4. DECIDE category mapping v2 (category_coverage output): accept smaller categories, or add more need-domain terms (Education, Financial, Health lost most).
5. Confirm with NCSS (open): parents for Homeless / Inmates / Victims of abuse (provisional, fallbacks stored); Caregiver + Chronically ill definitions; keep 'Elderly' name vs 'Seniors' (partner-breaking).
6. Measure luna run-to-run variance (3 repeats) before final gate numbers; mental-health precision on suite (general counselling over-tag) — consider prompt/definition tweak.
7. Non-regression check on other extracted fields (agency, phone, email, eligibility, description) if luna replaces gpt-5 in the extractor.
8. what_it_gives / scheme_type further tuning on dev half only; gate on test half (no fresh held-out set — user decision; treat gate as sanity check).
9. Gate report vs criteria (below) -> user sign-off. HARD GATE: no Phase 2 until sign-off.
10. Housekeeping: uv.lock for ncss_eval not committed; Jev scripts kept but arm dropped.

## STEP 0 — NAMING DECISION (2026-10-04, advisor-reviewed; awaiting user pick; taxonomy.py NOT to be renamed until chosen)
Filters: (1) NCSS label must be a true synonym, not a broader parent (parents stay in parent column); (2) clearer for Singapore users on public filter labels. Sector jargon (Groupwork, Casework/Case Management, Shelter provision) fails filter 2.
Rename candidates: see findings.md "Step 0 rename table". Each rename needs: alias map old->new, R6 partner list entry, keep old word in embedded text/definition (recall).

## PHASE 2 PLAN v2 (2026-10-04, user-approved; supersedes the "PHASE 2 (outline)" below)
Scope rules (user): UI = option 1 (our granular terms shown, NCSS parent stored only, not displayed). Dev vs prod data are out of sync (issue #446, to land first): this project changes and tests CODE on stg only. NO data writes (no dev or prod migration, no re-embed run) as part of this work. NCSS batch 2 is already fully ingested in prod (drop old "ingest batch 2" step).
Step A (gate): user reviews data/gold_review_prod.csv -> load as gold -> rescore luna-medium (tune prompt recall on dev half only) -> gate report -> user sign-off.
Step 1 (CODE, start now, parallel with gold review): 
  1a single vocabulary source of truth (dedupe scheme-processor/app/constants.py vs functions/new_scheme/constants.py; Slack review blocks read from it); 
  1b NCSS parent table + RENAMES/alias map in app code (static, never LLM); 
  1c extractor: new prompt with per-term definitions + strict json_schema enums, age bands derived in code; drop litellm drop_params risk (verify params are honoured); 
  1d alias-map normaliser: fail closed, log unmatched, replaces keyword-overlap fallback (extraction.py); 
  1e unit tests (secretless, `uv run --frozen pytest`) incl. old-term -> new-term alias cases, removed terms never emitted, age-band boundaries; 
  1f frontend/category mapping + firestore.indexes for new scheme_type terms (code only), partner serializer compatibility layer (R6) designed + tested with fixtures.
Step 2 (offline only): migration + re-embed SCRIPTS written and dry-run-tested against local JSON snapshots; execution against any live project is a separate, later decision (needs NCSS programme review, #446 parity, R6 partner notice).
Step 3 (later, not this project's PR): NCSS replies (7 no-match terms, Learning intervention def, Homeless/Inmates/Victims parents, Caregiver Support, canonical labels) -> finalise provisional flags.
Search quality: before/after check queries ("help for my maid", "elderly with dementia"); keep old words (elderly, maid) in definitions/embedded text so renames do not drop recall.

## NCSS FEEDBACK ROUND 2 (18 Sep who + 1 Oct intervention, issue comment 4 Oct) — 2026-10-04
**Principle (user, 2026-10-04): do NOT rename our terms just to follow NCSS when we have our own definition. Rename only if it makes meaning clearer / avoids confusion.** NCSS labels live in the parent column; our term names stay. Consequences: `Elderly` stays (Seniors = NCSS parent label only; no partner-breaking rename); `Legal Aid` scheme_type keeps its name, parent label = Justice & Legal Protection; label differences (Group Work/Groupwork etc.) are fixed in the parent strings, not in our terms.
Tension (comment sec.7 vs sec.3): vocabulary changes already proceeding on branch; only R5 re-tag/re-embed and merge to stg wait for NCSS programme review.

DONE in taxonomy.py (2026-10-04, uncommitted)
- who: Facing end of life -> no profile parent; Individuals struggling with loss -> no parent; MOVED_OUT_NEED_PARENT added (food -> Financial & Material Support, legal aid -> Justice & Legal Protection, shelter -> Housing & Shelter Support, mortgage -> Financial & Material Support).
- what_it_gives parents: Debt assistance -> Casework only; Transport subsidies, PWD benefits, Technology assistance, Financial assistance for housing -> Financial/Material Assistance only.
- Merged Referral + Information -> "Information and referral services". Split Tuition/Enrichment -> "Tuition" + "Enrichment programmes"; Home retrofitting & assistive tech -> "Home retrofitting" + "Assistive technology" (assistive tech -> Mobility Services is OUR assumption, provisional). Added "Learning intervention" (provisional; definition to confirm from NCSS deck). Removed Protection against violence, Child protection services, Identification and safety tagging, COVID-19 support (see REMOVED_FROM_WHAT_IT_GIVES).
- Provisional=True: the 7 no-match terms + Educational programmes (NCSS: review to find actual intervention) + Enrichment programmes, Home retrofitting, Assistive technology, Learning intervention. PROVISIONAL_INTERVENTION_PARENTS = Coaching, Community Dev/Outreach, Crisis Assessment & Intervention, Enrichment Activities, Mobility Services, Psychoeducation, Mentoring, Info & Communication Accessibility, Learning Intervention (Mentoring + ICA were missing from the issue comment: add).
- scheme_type: Legal Aid parent -> Justice & Legal Protection (NEEDS list updated).
- Counts now: who 46, what 53, scheme_type 37.

TODO (next) [2026-10-04: venv rebuilt; luna run on 100 prod schemes done, see findings]
0. Decide Learning intervention vs Educational programmes overlap (findings 2026-10-04); confirm Child and Youth Services; relabel what_it_gives gold; build alias map entries for prod drift ('Rehabilitation services', 'Technology assistance').
1. Pull Learning intervention + Justice & Legal Protection definitions from NCSS pptx (~/Downloads/2026-04-29 Programme Taxonomy V1.0.pptx); fix definition text.
2. Regenerate prompt_preview.md; the ncss_eval/.venv is broken (Bad CPU type) -> recreate with `rm -rf .venv && uv sync` (gitignored) then re-run luna on dev+test with new vocab. what_it_gives gold must be relabelled (removed/merged/split terms; scorer must map old gold -> new).
3. Skills training and job matching: keep only for programmes delivering both; else split to Training / Job Placement (Phase 2 review). Educational programmes parent TBD after review.
4. Open with NCSS: Homeless/Inmates/Victims parents; 7 no-match terms review; "Caregiver Support" = what_it_gives half of Respite care/Caregiver support (sheet reading) or scheme_type term; canonical label list; NCSS needs draft (compare with scheme_type branch when it arrives).
5. OPEN QUESTION (user): pregnancy. Email told NCSS "one pregnancy-related descriptor for Pregnant individuals in distress + Teenagers facing pregnancy". Branch keeps BOTH terms (granularity principle, age via bands). Confirm or merge.
6. Verbatim-search request from NCSS (1 Oct): user will reply separately. Before sharing check privacy policy/consent, scrub PII.
7. Add to R6 partner change list: merges/splits/removals above (no Elderly->Seniors rename). Confirm prod count of Identification and safety tagging.
8. Update GitHub issue comment: note no-rename principle, add Mentoring/ICA provisional, Educational programmes, assistive-tech assumption, verbatim request.

## HARD GATE criteria (revised)
luna-medium on test half: who micro P>=0.90 R>=0.85; what and scheme_type F1 >= ~0.80 (proposed, confirm); 0 out-of-vocab (enum-enforced); disability suite hard violations = 0 and PWD recall >= 0.9; age-band boundary tests pass; removed terms never emitted; category coverage diff accepted by user; spot-check ~20 disagreements by user.

## PHASE 2 (outline, detail after gate)
taxonomy single source of truth (dedupe scheme-processor/app/constants.py vs functions/new_scheme/constants.py; Slack review blocks) -> extractor + alias-map normalizer (fail closed, log) -> SCHEME_CATEGORY_MAPPING rebuild + catalog.py/firestore.indexes -> embedding text (reindex_embeddings) + search benchmark before/after -> migration script (dry-run, measure 109 live values coverage; schemes + schemeEntries) -> partner API compat R6 (CareCompass, Rosette) gates release -> frontend -> NCSS batch-2 ingest AFTER new vocab.

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| gh issue view GraphQL projectCards | 1 | --json --jq |
| xlsx path "Taxos" w/ double space guessed wrong | 1 | actual name has '&'; used glob |
| `uv run --with` in scheme-processor removed & recreated .venv (py3.12 miniconda) | 1 | gitignored; run `uv sync` in scheme-processor if env misbehaves. Use scratch venv for eval deps next time |
