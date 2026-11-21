"""patch_schemes: vocabulary and guard checks, dry run writes nothing, --write backs up and writes with a precondition."""

import json

import pytest

from scripts import patch_schemes as ps


class Snap:
    def __init__(self, doc_id, data, store):
        self.id, self._data, self.exists = doc_id, data, data is not None
        self.update_time = "t0"
        self.reference = Ref(doc_id, store)

    def to_dict(self):
        return dict(self._data)


class Ref:
    def __init__(self, doc_id, store):
        self.id, self.store = doc_id, store

    def get(self):
        return Snap(self.id, self.store.docs.get(self.id), self.store)

    def update(self, data, option=None):
        if option is not None and self.store.fail_precondition:
            raise RuntimeError("FailedPrecondition")
        self.store.writes.append((self.id, data, option))


class FakeDb:
    def __init__(self, docs, fail_precondition=False):
        self.docs, self.writes, self.fail_precondition = docs, [], fail_precondition

    def collection(self, name):
        assert name == "schemes"
        return self

    def document(self, doc_id):
        return Ref(doc_id, self)

    def write_option(self, **kwargs):
        return kwargs


HCG = {"summary": "Monthly cash grant", "llm_description": "up to $400 per month", "last_scraped_update": "old"}


@pytest.fixture
def run(monkeypatch, tmp_path):
    """Run main() against a FakeDb with a patch file; returns (db, backup dir)."""

    def _run(patch, docs, *flags, fail_precondition=False):
        db = FakeDb(docs, fail_precondition)
        monkeypatch.setattr(ps, "load_environment", lambda env: env)
        monkeypatch.setattr(ps, "firestore_client", lambda _name: db)
        path = tmp_path / "patch.json"
        path.write_text(json.dumps(patch))
        ps.main(["dev", str(path), "--backup-dir", str(tmp_path / "backups"), *flags])
        return db, tmp_path / "backups"

    return _run


def patch_hcg(**overrides):
    entry = {
        "label": "HCG",
        "expect": {"llm_description": "$400"},
        "set": {"summary": "Monthly cash grant of $200 to $600"},
    }
    return {"hcg": {**entry, **overrides}}


def test_dry_run_writes_nothing(run):
    db, backups = run(patch_hcg(), {"hcg": HCG})
    assert db.writes == []
    assert not backups.exists()


def test_write_backs_up_old_values_then_stamps_with_a_precondition(run):
    db, backups = run(patch_hcg(), {"hcg": HCG}, "--write")
    [(doc_id, data, option)] = db.writes
    assert doc_id == "hcg"
    assert data["summary"] == "Monthly cash grant of $200 to $600"
    assert data[ps.STAMP_FIELD] is ps.SERVER_TIMESTAMP
    assert option == {"last_update_time": "t0"}
    [backup] = backups.iterdir()
    assert json.loads(backup.read_text()) == {"hcg": {"summary": "Monthly cash grant", "last_scraped_update": "old"}}


def test_failed_guard_skips_the_scheme(run, capsys):
    db, _ = run(patch_hcg(expect={"llm_description": "$800"}), {"hcg": HCG}, "--write")
    assert db.writes == []
    assert "guard failed" in capsys.readouterr().out


def test_scheme_edited_since_the_read_is_skipped_not_overwritten(run, capsys):
    db, _ = run(patch_hcg(), {"hcg": HCG}, "--write", fail_precondition=True)
    assert db.writes == []
    assert "wrote 0 of 1" in capsys.readouterr().out


def test_unchanged_fields_are_not_written(run):
    db, _ = run(patch_hcg(set={"summary": "Monthly cash grant"}), {"hcg": HCG}, "--write")
    assert db.writes == []


def test_off_vocabulary_tags_are_refused_before_any_read(run):
    with pytest.raises(SystemExit, match="off-vocabulary"):
        run(patch_hcg(set={"scheme_type": ["Child and Youth Services"]}), {"hcg": HCG})


def test_tags_from_the_current_vocabulary_pass(run):
    db, _ = run(patch_hcg(set={"scheme_type": ["Caregiver Support"]}), {"hcg": HCG}, "--write")
    assert db.writes[0][1]["scheme_type"] == ["Caregiver Support"]


def test_prod_write_needs_the_project_confirmed():
    with pytest.raises(SystemExit):
        ps.parse_args(["prod", "patch.json", "--write"])
    assert ps.parse_args(["prod", "patch.json", "--write", "--confirm-project", "schemessg"]).write


def test_restore_puts_old_values_back_and_restamps(monkeypatch, tmp_path):
    db = FakeDb({"hcg": HCG})
    monkeypatch.setattr(ps, "load_environment", lambda env: env)
    monkeypatch.setattr(ps, "firestore_client", lambda _name: db)
    backup = tmp_path / "backup.json"
    backup.write_text(json.dumps({"hcg": {"summary": "Monthly cash grant", "last_scraped_update": "old"}}))
    ps.main(["dev", "--restore", str(backup)])
    assert db.writes == []
    ps.main(["dev", "--restore", str(backup), "--write"])
    [(doc_id, data, _)] = db.writes
    assert data == {"summary": "Monthly cash grant", ps.STAMP_FIELD: ps.SERVER_TIMESTAMP}


def test_default_backups_land_in_the_gitignored_data_folder():
    assert ps.DEFAULT_BACKUP_DIR.parts[-2:] == ("data", "patches")
    assert (ps.DEFAULT_BACKUP_DIR.parents[1] / "AGENTS.md").exists()
