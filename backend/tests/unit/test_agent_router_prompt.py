from agent.prompts.router import ROUTER_AGENT_SYSTEM_TEMPLATE


ORIGINAL_ISSUE_EMAIL_REQUEST = "Draft an email asking about respite care for a dementia caregiver."


def test_router_prompt_routes_email_drafting_to_draft_email_skill():
    assert "draft, rewrite, or polish an email" in ROUTER_AGENT_SYSTEM_TEMPLATE
    assert 'load_skills with skill="draft_email"' in ROUTER_AGENT_SYSTEM_TEMPLATE
    assert "before composing the email" in ROUTER_AGENT_SYSTEM_TEMPLATE


def test_router_prompt_includes_stray_tamil_regression_rule_for_email_drafts():
    assert ORIGINAL_ISSUE_EMAIL_REQUEST.startswith("Draft an email")
    assert "stray Tamil characters in an English reply" in ROUTER_AGENT_SYSTEM_TEMPLATE
    assert "out-of-place characters from unrelated writing systems" in ROUTER_AGENT_SYSTEM_TEMPLATE
