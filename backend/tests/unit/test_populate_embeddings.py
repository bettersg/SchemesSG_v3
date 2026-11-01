"""populate_embeddings script: runs the shared reindex against the right project, with a prod confirmation."""

import pandas as pd
import pytest
from utils.reindex_embeddings import build_desc_booster

from scripts import populate_embeddings as pe


@pytest.fixture
def stubbed(monkeypatch, tmp_path):
    """Env files in tmp_path; the reindex and the Firestore client are recorded instead of run."""
    calls = {}
    monkeypatch.setattr(pe, "FUNCTIONS_DIR", tmp_path)
    monkeypatch.setattr(pe, "firestore_client", lambda: "db")

    def reindex(db):
        calls["db"] = db
        return {"success": True, "indexed_schemes": 1}

    monkeypatch.setattr(pe, "reindex_embeddings", reindex)
    (tmp_path / ".env.dev").write_text("FB_PROJECT_ID=schemessg-v3-dev\n")
    (tmp_path / ".env.prod").write_text("FB_PROJECT_ID=schemessg\n")
    return calls


def test_dev_runs_the_shared_reindex(stubbed):
    assert pe.main(["--dev"]) == {"success": True, "indexed_schemes": 1}
    assert stubbed["db"] == "db"


def test_env_file_naming_another_project_is_refused(stubbed, tmp_path):
    (tmp_path / ".env.dev").write_text("FB_PROJECT_ID=schemessg\n")
    with pytest.raises(SystemExit):
        pe.main(["--dev"])
    assert "db" not in stubbed


def test_prod_needs_typed_confirmation(stubbed, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "no")
    with pytest.raises(SystemExit):
        pe.main(["--prod"])
    assert "db" not in stubbed

    monkeypatch.setattr("builtins.input", lambda _prompt: "yes")
    assert pe.main(["--prod"])["success"]


def test_list_tag_fields_build_embedding_text():
    """The old script's own builder raised ValueError on list fields (pd.notna on a list)."""
    row = pd.Series(
        {
            "scheme": "Foster care",
            "who_is_it_for": ["Children", "Caregivers"],
            "scheme_type": ["Fostering and alternative care"],
        }
    )
    assert build_desc_booster(row) == "Foster care Children, Caregivers Fostering and alternative care"
