"""Unit tests for the consolidated scheme review Slack block builder."""

from new_scheme.new_scheme_blocks import (
    build_new_scheme_review_message,
    build_scheme_review_message,
    build_scheme_update_review_message,
)


def _base_payload() -> dict:
    return {
        "scheme_name": "Test Scheme",
        "scheme_url": "https://example.com/scheme",
        "scraped_text": "Some scraped text content.",
        "llm_fields": {
            "llm_description": "A test description.",
            "who_is_it_for": ["seniors", "families"],
            "what_it_gives": ["cash", "vouchers"],
            "scheme_type": ["financial"],
        },
        "planning_area": "Bedok",
        "processing_status": "completed",
        "error": None,
    }


def _block_types(msg: dict) -> list[str]:
    return [b.get("type") for b in msg["blocks"]]


def _first_section_text(msg: dict) -> str:
    for block in msg["blocks"]:
        if block.get("type") == "section" and block.get("text"):
            return block["text"]["text"]
    return ""


def _header_text(msg: dict) -> str:
    for block in msg["blocks"]:
        if block.get("type") == "header":
            return block["text"]["text"]
    return ""


def _action_labels(msg: dict) -> list[str]:
    for block in msg["blocks"]:
        if block.get("type") == "actions":
            return [el["text"]["text"] for el in block["elements"]]
    return []


def test_new_and_update_share_body_block_sequence():
    """Same scraped + LLM fields + description blocks; only header + first section + buttons differ."""
    payload = _base_payload()
    new_msg = build_scheme_review_message("doc-1", payload, flavor="new")
    update_payload = {
        **payload,
        "target_scheme_id": "scheme-abc",
        "original_data": {"oldLink": "https://old-dead.example/"},
    }
    update_msg = build_scheme_review_message("doc-1", update_payload, flavor="update")

    assert _block_types(new_msg) == _block_types(update_msg)


def test_new_header_and_buttons():
    msg = build_scheme_review_message("doc-1", _base_payload(), flavor="new")
    assert _header_text(msg) == "New Scheme Submission"
    assert _action_labels(msg) == ["Review & Approve", "Reject"]
    assert msg["text"] == "New scheme submission: Test Scheme"


def test_update_header_and_buttons():
    payload = {
        **_base_payload(),
        "target_scheme_id": "scheme-abc",
        "original_data": {"oldLink": "https://old-dead.example/"},
    }
    msg = build_scheme_review_message("doc-1", payload, flavor="update")
    assert _header_text(msg) == "Scheme Update — Replace Dead Link"
    assert _action_labels(msg) == ["Approve Update", "Reject Update"]
    assert "scheme-abc" in msg["text"]


def test_update_top_section_shows_target_and_old_url():
    payload = {
        **_base_payload(),
        "target_scheme_id": "scheme-abc",
        "original_data": {"oldLink": "https://old-dead.example/"},
    }
    msg = build_scheme_review_message("doc-1", payload, flavor="update")
    section = _first_section_text(msg)
    assert "scheme-abc" in section
    assert "https://old-dead.example/" in section
    assert "https://example.com/scheme" in section


def test_update_top_section_unknown_old_url_when_missing():
    payload = {
        **_base_payload(),
        "target_scheme_id": "scheme-abc",
        "original_data": {},
    }
    msg = build_scheme_review_message("doc-1", payload, flavor="update")
    section = _first_section_text(msg)
    assert "_unknown_" in section


def test_action_ids_same_across_flavors():
    """Approval handler dispatches on entry typeOfRequest, so action_ids must match."""
    new_msg = build_scheme_review_message("doc-1", _base_payload(), flavor="new")
    update_payload = {
        **_base_payload(),
        "target_scheme_id": "scheme-abc",
        "original_data": {"oldLink": "x"},
    }
    update_msg = build_scheme_review_message("doc-1", update_payload, flavor="update")

    def _ids(msg):
        for block in msg["blocks"]:
            if block.get("type") == "actions":
                return [el["action_id"] for el in block["elements"]]
        return []

    assert _ids(new_msg) == _ids(update_msg) == ["review_new_scheme", "reject_new_scheme"]


def test_legacy_wrappers_route_to_correct_flavor():
    payload = _base_payload()
    new_legacy = build_new_scheme_review_message("doc-1", payload)
    new_direct = build_scheme_review_message("doc-1", payload, flavor="new")
    assert new_legacy == new_direct

    upd_payload = {**payload, "target_scheme_id": "s-1", "original_data": {"oldLink": "x"}}
    update_legacy = build_scheme_update_review_message("doc-1", upd_payload)
    update_direct = build_scheme_review_message("doc-1", upd_payload, flavor="update")
    assert update_legacy == update_direct


def test_scraping_failed_status_emoji():
    payload = {**_base_payload(), "processing_status": "scraping_failed", "error": "404"}
    msg = build_scheme_review_message("doc-1", payload, flavor="update")
    elements = next(b for b in msg["blocks"] if b.get("type") == "context")["elements"]
    status_line = next(e["text"] for e in elements if ":warning:" in e["text"])
    assert "404" in status_line
