"""Reclassification script: frozen-result reuse, old-vs-new diff, review flags and the write plan."""

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts/ncss_eval"))
sys.path.insert(0, str(BACKEND / "scheme-processor"))

import reclassify as rc  # noqa: E402

SCHEME = {
    "id": "a1", "scheme": "Legal clinic", "agency": "Law Society", "description": "Free legal advice.", "llm_description": None,
    "summary": None, "eligibility": "Low income", "status": None,
    "who_is_it_for": ["Elderly"], "what_it_gives": ["Referral services"], "scheme_type": ["Legal Aid", "Healthcare"],
}


def test_result_is_reused_only_while_input_and_prompt_are_unchanged():
    result = {"input_hash": rc.input_hash(SCHEME)}
    assert not rc.needs_classification(SCHEME, result)
    assert rc.needs_classification(SCHEME, result, force=True)
    assert rc.needs_classification(SCHEME, None)
    assert rc.needs_classification({**SCHEME, "description": "Edited text."}, result)


def test_old_tags_are_compared_in_the_new_vocabulary():
    old = rc.old_in_new_vocabulary(SCHEME)
    assert old["who_is_it_for"] == ["Seniors"]
    assert old["what_it_gives"] == ["Information and referral services", "Legal aid and services"]
    assert old["scheme_type"] == ["Healthcare"]
    same = {"who_is_it_for": ["Seniors"], "what_it_gives": old["what_it_gives"], "scheme_type": ["Healthcare"]}
    assert rc.changed_fields(SCHEME, same) == []
    assert rc.changed_fields(SCHEME, {**same, "scheme_type": ["Healthcare", "Financial Assistance"]}) == ["scheme_type"]


def test_new_tags_derive_age_bands_and_return_none_for_empty_fields():
    raw = json.dumps(
        {"who_is_it_for": ["Persons with disabilities (PWDs)"], "what_it_gives": ["Counselling"], "scheme_type": [],
         "age_min": 70, "age_max": None, "rationale": "r"})
    tags = rc.new_tags(raw)
    assert tags["who_is_it_for"] == ["Persons with disabilities (PWDs)", "Seniors"]
    assert tags["scheme_type"] is None and tags["age_min"] == 70


def test_review_flags_put_sensitive_schemes_first():
    result = {"who_is_it_for": ["Inmates", "Victims of abuse or harassment"], "what_it_gives": [], "scheme_type": ["Community Funding"]}
    flags = rc.review_flags({**SCHEME, "scheme_type": ["COVID-19 Support"]}, result)
    assert any("covid-19" in f for f in flags)
    assert "victims of abuse" in flags
    assert not any("provisional" in f for f in flags)  # provisional parents are listed on the Term counts sheet, not flagged per row
    assert rc.review_flags(SCHEME, {"who_is_it_for": ["Seniors"], "what_it_gives": ["Counselling"], "scheme_type": ["Healthcare"]}) == []
    assert rc.review_flags(SCHEME, {"who_is_it_for": None, "what_it_gives": None, "scheme_type": None}) == ["no tags"]


def test_apply_plan_only_touches_schemes_whose_tags_differ():
    snapshot = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": None, "scheme_type": ["Healthcare"]},
                "b": {"who_is_it_for": ["Youth"], "what_it_gives": ["Counselling"], "scheme_type": ["Healthcare"]},
                "c": {"who_is_it_for": ["Youth"], "what_it_gives": None, "scheme_type": None}}
    results = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": None, "scheme_type": ["Healthcare"]},
               "b": {"who_is_it_for": ["Youth"], "what_it_gives": ["Counselling", "Befriending services"], "scheme_type": ["Healthcare"]}}
    assert rc.apply_plan(snapshot, results) == {"b": {"what_it_gives": ["Counselling", "Befriending services"]}}


def test_an_empty_model_field_never_wipes_existing_tags():
    snapshot = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": ["Counselling"], "scheme_type": None}}
    results = {"a": {"who_is_it_for": ["Seniors"], "what_it_gives": None, "scheme_type": ["Healthcare"]}}
    assert rc.apply_plan(snapshot, results) == {"a": {"scheme_type": ["Healthcare"]}}
    assert rc.empty_over_existing(snapshot, results) == [("a", "what_it_gives")]


def test_term_counts_count_each_scheme_once():
    counts = rc.term_counts([{"who_is_it_for": ["Youth", "Youth"]}, {"who_is_it_for": ["Youth"]}, {}])
    assert counts["who_is_it_for"]["Youth"] == 2


def test_stale_results_are_rejected_by_hash_and_vocabulary_version():
    fresh = {"id": "a1", "input_hash": rc.input_hash(SCHEME), "taxonomy_version": rc.tx.TAXONOMY["version"]}
    edited = {"id": "a1", "input_hash": rc.input_hash({**SCHEME, "description": "Edited after the run"}), "taxonomy_version": rc.tx.TAXONOMY["version"]}
    old_vocab = {**fresh, "taxonomy_version": "v1-old"}
    assert rc.stale_results({"a1": SCHEME}, {"a1": fresh}) == []
    assert rc.stale_results({"a1": SCHEME}, {"a1": edited}) == [("a1", "input_hash")]
    assert rc.stale_results({"a1": SCHEME}, {"a1": old_vocab}) == [("a1", "taxonomy_version")]


def test_live_drift_detects_an_edit_after_the_snapshot():
    assert rc.live_drift(SCHEME, dict(SCHEME)) is False
    assert rc.live_drift(SCHEME, {**SCHEME, "eligibility": "Everyone"}) is True
    assert rc.live_drift(SCHEME, {**SCHEME, "who_is_it_for": ["Seniors"]}) is True


class _Doc:
    def __init__(self, sid, data):
        self.id, self._data, self.exists = sid, data, True

    def to_dict(self):
        return dict(self._data)


class _Db:
    """Just enough Firestore for cmd_apply: get_all, document refs and a batch that records updates."""

    def __init__(self, docs):
        self.docs, self.updates = docs, {}

    def collection(self, _name):
        return self

    def document(self, sid):
        return sid

    def get_all(self, refs):
        return [_Doc(sid, self.docs[sid]) for sid in refs if sid in self.docs]

    def batch(self):
        return self

    def update(self, sid, data):
        self.updates[sid] = data

    def commit(self):
        pass


def _apply_args(env, write=True, confirm=None):
    return rc.argparse.Namespace(env=env, write=write, confirm_project=confirm)


def _stub_apply(monkeypatch, tmp_path, db=None):
    snapshot = {"a1": SCHEME}
    result = {"id": "a1", "who_is_it_for": ["Seniors"], "what_it_gives": ["Information and referral services"],
              "scheme_type": ["Healthcare"], "taxonomy_version": rc.tx.TAXONOMY["version"], "input_hash": rc.input_hash(SCHEME)}
    monkeypatch.setattr(rc, "OUT", tmp_path)
    monkeypatch.setattr(rc, "_snapshot", lambda env="prod": snapshot)
    monkeypatch.setattr(rc, "_latest_results", lambda: {"a1": result})

    def firestore(env):
        if db is None:
            raise AssertionError(f"_firestore({env}) must not be reached")
        return db

    monkeypatch.setattr(rc, "_firestore", firestore)


def test_prod_write_needs_the_project_named(monkeypatch, tmp_path):
    _stub_apply(monkeypatch, tmp_path)
    for confirm in (None, "schemessg-v3-dev"):
        try:
            rc.cmd_apply(_apply_args("prod", confirm=confirm))
        except SystemExit as stop:
            assert "--confirm-project schemessg" in str(stop)
        else:
            raise AssertionError("prod write ran without --confirm-project schemessg")
        try:
            rc.cmd_restore(rc.argparse.Namespace(env="prod", backup=str(tmp_path / "none.jsonl"), write=True, confirm_project=confirm))
        except SystemExit as stop:
            assert "--confirm-project schemessg" in str(stop)
        else:
            raise AssertionError("prod restore ran without --confirm-project schemessg")


def test_apply_stamps_tags_updated_at_and_backs_up_the_live_tags(monkeypatch, tmp_path):
    from firebase_admin import firestore

    db = _Db({"a1": {k: SCHEME.get(k) for k in rc.SNAPSHOT_KEYS}})
    _stub_apply(monkeypatch, tmp_path, db)
    rc.cmd_apply(_apply_args("prod", confirm="schemessg"))

    assert db.updates["a1"]["tags_updated_at"] is firestore.SERVER_TIMESTAMP
    assert db.updates["a1"]["who_is_it_for"] == ["Seniors"]
    (backup,) = tmp_path.glob("backup-prod-*.jsonl")
    row = json.loads(backup.read_text())
    assert row["who_is_it_for"] == ["Elderly"] and row["tags_updated_at"] is None
