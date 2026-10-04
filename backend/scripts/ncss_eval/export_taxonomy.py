"""Generate the canonical taxonomy JSON from taxonomy.py and vendor it into both deploy units.
Cloud Run (scheme-processor) and Firebase Functions each package only their own directory, so each gets a copy;
tests/unit/test_taxonomy_sync.py asserts the copies equal this generator's output.
usage (from backend/scripts/ncss_eval): python export_taxonomy.py [--check]"""
import ast, json, sys
from pathlib import Path
import taxonomy as tx

BACKEND = Path(__file__).resolve().parents[2]
TARGETS = [BACKEND / "scheme-processor/app/taxonomy_data.json", BACKEND / "functions/new_scheme/taxonomy_data.json"]
LEGACY_CONSTANTS = BACKEND / "functions/new_scheme/constants.py"
VERSION = "v2-draft-2026-10-04"  # bump when NCSS review / gate changes the vocabulary


def legacy_category_mapping():
    """Pre-v2 category lists, kept so old-vocabulary data still lands in a category until the data is migrated.
    Read from the source literal (not imported): constants.py itself loads the JSON this script generates."""
    tree = ast.parse(LEGACY_CONSTANTS.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "LEGACY_SCHEME_CATEGORY_MAPPING":
            return ast.literal_eval(node.value)
    raise SystemExit("LEGACY_SCHEME_CATEGORY_MAPPING not found in " + str(LEGACY_CONSTANTS))


def build():
    v2 = {k: list(v) for k, v in tx.SCHEME_CATEGORY_MAPPING_V2.items()}
    flat = [t for v in v2.values() for t in v]
    live = [t.name for t in tx.SCHEME_TYPE]
    assert sorted(flat) == sorted(live), "category_mapping must place every scheme_type in exactly one category"
    for cat, terms in v2.items():
        assert len(terms) <= 30
    # pre-v2 terms still present in un-migrated data: category lookups accept them too (kept out of the v2 partition)
    legacy = {k: [t for t in v if t not in live] for k, v in legacy_category_mapping().items()}
    for cat in v2:
        assert len(v2[cat]) + len(legacy.get(cat, [])) <= 30, f"{cat}: exceeds Firestore array-contains-any limit"
    term = lambda t: {"name": t.name, "definition": t.definition, "provisional": t.provisional, "note": t.note}
    return {
        "version": VERSION,
        "age_bands": [{"term": t, "min": lo, "max": hi} for t, lo, hi in tx.AGE_BAND_TERMS],
        "who_is_it_for": [{**term(t), "age_group": list(t.age_group), "profile": list(t.profile), "fallback_profile": list(t.fallback_profile)} for t in tx.WHO_IS_IT_FOR],
        "what_it_gives": [{**term(t), "intervention": list(t.profile)} for t in tx.WHAT_IT_GIVES],
        "scheme_type": [{**term(t), "need": list(t.profile)} for t in tx.SCHEME_TYPE],
        "renames": tx.RENAMES,
        "legacy_aliases": tx.LEGACY_ALIASES,
        "moved_out_need_parent": tx.MOVED_OUT_NEED_PARENT,
        "provisional_intervention_parents": sorted(tx.PROVISIONAL_INTERVENTION_PARENTS),
        # embedding text keeps the pre-rename word next to the new term so search recall does not drop
        "embed_synonyms": {new: old for old, new in tx.RENAMES.items()},
        "category_mapping": v2,
        "legacy_category_mapping": legacy,
    }


if __name__ == "__main__":
    out = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        sys.exit(0 if all(p.exists() and p.read_text() == out for p in TARGETS) else 1)
    for p in TARGETS:
        p.write_text(out)
        print("wrote", p)
