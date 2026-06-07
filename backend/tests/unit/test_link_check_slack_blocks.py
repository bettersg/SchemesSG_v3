"""Unit tests for batch_jobs.slack_blocks.build_link_check_summary_message."""

import pytest

from batch_jobs.slack_blocks import build_link_check_summary_message


def _dead_link(n: int) -> dict:
    return {
        "doc_id": f"doc-{n}",
        "scheme_name": f"Scheme {n}",
        "link": f"https://example.com/{n}",
        "error": "HTTP 404",
    }


def _restored_link(n: int) -> dict:
    return {
        "doc_id": f"rdoc-{n}",
        "scheme_name": f"Restored {n}",
        "link": f"https://example.com/restored/{n}",
        "previous_error": "HTTP 500",
    }


def _results(total: int, alive: int, dead: int, restored: int = 0) -> dict:
    return {
        "total_checked": total,
        "alive_count": alive,
        "dead_count": dead,
        "restored_count": restored,
        "duration_seconds": 60,
    }


def _reindex_success(indexed: int = 400) -> dict:
    return {"success": True, "indexed_schemes": indexed, "skipped_inactive": 10}


def test_block_count_never_exceeds_slack_limit_with_many_dead_links():
    dead = [_dead_link(i) for i in range(80)]
    msg = build_link_check_summary_message(
        results=_results(500, 420, 80),
        dead_links=dead,
        reindex_result=_reindex_success(),
    )
    assert len(msg["blocks"]) <= 50


def test_zero_links_produces_no_link_sections():
    msg = build_link_check_summary_message(
        results=_results(100, 100, 0),
        dead_links=[],
        reindex_result=_reindex_success(),
    )
    texts = [b.get("text", {}).get("text", "") for b in msg["blocks"] if b.get("type") == "section"]
    assert not any("Dead Links Detected" in t for t in texts)
    assert not any("Restored Links" in t for t in texts)


def test_small_dead_list_fits_in_one_chunk_with_all_entries_visible():
    dead = [_dead_link(i) for i in range(5)]
    msg = build_link_check_summary_message(
        results=_results(100, 95, 5),
        dead_links=dead,
        reindex_result=_reindex_success(),
    )
    all_text = "\n".join(b.get("text", {}).get("text", "") for b in msg["blocks"] if b.get("type") == "section")
    for i in range(5):
        assert f"Scheme {i}" in all_text
        assert f"doc-{i}" in all_text


def test_prod_shape_47_dead_and_4_restored_posts_all_entries_without_truncation():
    dead = [_dead_link(i) for i in range(47)]
    restored = [_restored_link(i) for i in range(4)]
    msg = build_link_check_summary_message(
        results=_results(494, 447, 47, restored=4),
        dead_links=dead,
        reindex_result=_reindex_success(),
        restored_links=restored,
    )
    assert len(msg["blocks"]) <= 50
    all_text = "\n".join(b.get("text", {}).get("text", "") for b in msg["blocks"] if b.get("type") == "section")
    for i in range(47):
        assert f"doc-{i}" in all_text
    for i in range(4):
        assert f"rdoc-{i}" in all_text
    # No truncation notice for the prod shape
    context_texts = [
        el.get("text", "") for b in msg["blocks"] if b.get("type") == "context" for el in b.get("elements", [])
    ]
    assert not any("omitted" in t for t in context_texts)


def test_huge_dead_list_produces_truncation_notice_citing_omitted_count():
    dead = [_dead_link(i) for i in range(500)]
    msg = build_link_check_summary_message(
        results=_results(600, 100, 500),
        dead_links=dead,
        reindex_result=_reindex_success(),
    )
    assert len(msg["blocks"]) <= 50
    # Last block should be a truncation notice
    last = msg["blocks"][-1]
    assert last["type"] == "context"
    notice_text = last["elements"][0]["text"]
    assert "omitted" in notice_text
    assert "GCP logs" in notice_text


@pytest.mark.parametrize("dead_count,restored_count", [(0, 0), (5, 0), (47, 4), (80, 0), (500, 0)])
def test_every_section_text_stays_under_slack_3000_char_cap(dead_count, restored_count):
    dead = [_dead_link(i) for i in range(dead_count)]
    restored = [_restored_link(i) for i in range(restored_count)]
    msg = build_link_check_summary_message(
        results=_results(1000, 1000 - dead_count, dead_count, restored=restored_count),
        dead_links=dead,
        reindex_result=_reindex_success(),
        restored_links=restored,
    )
    for block in msg["blocks"]:
        if block.get("type") == "section":
            assert len(block["text"]["text"]) <= 3000


def test_restored_links_are_also_chunked_symmetrically():
    # 80 restored should be chunked the same way as 80 dead would be
    restored = [_restored_link(i) for i in range(80)]
    msg = build_link_check_summary_message(
        results=_results(500, 500, 0, restored=80),
        dead_links=[],
        reindex_result=_reindex_success(),
        restored_links=restored,
    )
    assert len(msg["blocks"]) <= 50
    # No restored doc id should be truncated if we're well under the 50 cap
    # (80 restored / 10 per chunk = 8 chunks; plus header/summary/divider/header/context/reindex ≈ 14 blocks total)
    all_text = "\n".join(b.get("text", {}).get("text", "") for b in msg["blocks"] if b.get("type") == "section")
    for i in range(80):
        assert f"rdoc-{i}" in all_text


@pytest.mark.parametrize("dead_count,restored_count", [(0, 0), (5, 0), (47, 4), (80, 0), (500, 0)])
def test_every_returned_block_has_valid_slack_shape(dead_count, restored_count):
    dead = [_dead_link(i) for i in range(dead_count)]
    restored = [_restored_link(i) for i in range(restored_count)]
    msg = build_link_check_summary_message(
        results=_results(1000, 1000 - dead_count, dead_count, restored=restored_count),
        dead_links=dead,
        reindex_result=_reindex_success(),
        restored_links=restored,
    )
    for block in msg["blocks"]:
        assert "type" in block
        if block["type"] == "section":
            assert "text" in block
            assert block["text"].get("type") in ("mrkdwn", "plain_text")
            assert isinstance(block["text"].get("text"), str)
        elif block["type"] == "header":
            assert block["text"]["type"] == "plain_text"
            assert isinstance(block["text"]["text"], str)
        elif block["type"] == "context":
            assert "elements" in block
            assert all("type" in el and "text" in el for el in block["elements"])
        elif block["type"] == "divider":
            pass
        else:
            raise AssertionError(f"Unexpected block type: {block['type']}")
