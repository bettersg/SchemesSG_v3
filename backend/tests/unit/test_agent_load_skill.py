import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


def _load_skill_module():
    module_path = Path(__file__).resolve().parents[2] / "functions" / "agent" / "tools" / "load_skill.py"
    spec = importlib.util.spec_from_file_location("agent_load_skill_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


load_skill = _load_skill_module()


def test_load_skills_draft_email_returns_email_prompt_only():
    payload = load_skill._build_skills_payload("draft_email")

    assert payload["skill"] == "draft_email"
    assert set(payload["skills"]) == {"draft_email"}
    assert "stray Tamil characters" in payload["skills"]["draft_email"]
    assert "Subject" not in payload["skills"]["draft_email"]
    assert "subject line" in payload["skills"]["draft_email"]


def test_load_skills_all_includes_draft_email():
    payload = load_skill._build_skills_payload("all")

    assert "clarification_questions" in payload["skills"]
    assert "summary_succinct_answer" in payload["skills"]
    assert "draft_email" in payload["skills"]


def test_load_skills_rejects_unknown_skill_name():
    with pytest.raises(ValidationError):
        load_skill.LoadSkillsInput(skill="unknown")
