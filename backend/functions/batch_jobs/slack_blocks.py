"""
Slack Block Kit builders for link check & reindex batch job.

Builds summary messages for link health check results.
"""

from typing import Any, Callable, Dict, List


MAX_LINKS_PER_BLOCK = 10
SLACK_MAX_BLOCKS = 50


def _format_dead_link(link: Dict[str, Any]) -> str:
    doc_id = link.get("doc_id", "Unknown")
    scheme_name = link.get("scheme_name", "Unknown")
    link_url = link.get("link", "")
    error = link.get("error", "Unknown error")
    return f"• *{scheme_name}*\n  ID: `{doc_id}`\n  Link: {link_url}\n  Error: _{error}_"


def _format_restored_link(link: Dict[str, Any]) -> str:
    doc_id = link.get("doc_id", "Unknown")
    scheme_name = link.get("scheme_name", "Unknown")
    link_url = link.get("link", "")
    previous_error = link.get("previous_error", "Unknown")
    return f"• *{scheme_name}*\n  ID: `{doc_id}`\n  Link: {link_url}\n  Previous error: _{previous_error}_"


def _chunked_link_blocks(links: List[Dict[str, Any]], formatter: Callable[[Dict[str, Any]], str]) -> List[dict]:
    """Group links into Slack section blocks, up to MAX_LINKS_PER_BLOCK per block."""
    blocks = []
    for i in range(0, len(links), MAX_LINKS_PER_BLOCK):
        chunk = links[i : i + MAX_LINKS_PER_BLOCK]
        text = "\n".join(formatter(link) for link in chunk)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
    return blocks


def _enforce_block_cap(blocks: List[dict]) -> List[dict]:
    """Truncate blocks to Slack's 50-block limit, adding an overflow notice if truncated."""
    if len(blocks) <= SLACK_MAX_BLOCKS:
        return blocks
    omitted = len(blocks) - (SLACK_MAX_BLOCKS - 1)
    truncated = blocks[: SLACK_MAX_BLOCKS - 1]
    truncated.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":warning: _… and {omitted} more entries omitted. Check GCP logs for the full list._",
                }
            ],
        }
    )
    return truncated


def build_link_check_summary_message(
    results: Dict[str, Any],
    dead_links: List[Dict[str, Any]],
    reindex_result: Dict[str, Any],
    restored_links: List[Dict[str, Any]] = None,
) -> dict:
    """
    Build Slack message summarizing link check and reindex results.

    Args:
        results: Link check summary stats
        dead_links: List of dead link details
        reindex_result: Embeddings reindex result
        restored_links: List of restored link details (previously inactive)

    Returns:
        Slack message payload with blocks
    """
    if restored_links is None:
        restored_links = []

    total_checked = results.get("total_checked", 0)
    alive_count = results.get("alive_count", 0)
    dead_count = results.get("dead_count", 0)
    restored_count = results.get("restored_count", 0)
    duration = results.get("duration_seconds", 0)

    # Format duration nicely
    if duration >= 60:
        duration_str = f"{duration / 60:.1f} minutes"
    else:
        duration_str = f"{duration:.0f} seconds"

    # Build summary text
    summary_text = (
        f"*Summary:*\n"
        f"Total schemes checked: *{total_checked}*\n"
        f":white_check_mark: Active links: *{alive_count}*\n"
        f":x: Dead links found: *{dead_count}*\n"
    )
    if restored_count > 0:
        summary_text += f":recycle: Restored from inactive: *{restored_count}*\n"
    summary_text += f":stopwatch: Duration: *{duration_str}*"

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "Link Check & Reindex Complete", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary_text}},
    ]

    # Add restored links section if any
    if restored_links:
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Restored Links ({len(restored_links)}) - previously inactive:*"},
            }
        )
        blocks.extend(_chunked_link_blocks(restored_links, _format_restored_link))
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": ":recycle: Status restored to active for these schemes"}],
            }
        )

    # Add dead links section if any found
    if dead_links:
        blocks.append({"type": "divider"})
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Dead Links Detected ({len(dead_links)}):*"}}
        )
        blocks.extend(_chunked_link_blocks(dead_links, _format_dead_link))
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": ":warning: Status updated to 'inactive' for all dead links"}],
            }
        )

    # Add reindex result
    blocks.append({"type": "divider"})

    if reindex_result.get("success"):
        reindex_text = (
            f":arrows_counterclockwise: *Embeddings Reindex:* Complete\n"
            f"• Schemes indexed: {reindex_result.get('indexed_schemes', 0)}\n"
            f"• Inactive skipped: {reindex_result.get('skipped_inactive', 0)}"
        )
    else:
        reindex_text = f":x: *Embeddings Reindex:* Failed\n• Error: {reindex_result.get('error', 'Unknown')}"

    blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": reindex_text}})

    # Build fallback text
    fallback_text = f"Link Check Complete: {alive_count} active, {dead_count} dead"
    if restored_count > 0:
        fallback_text += f", {restored_count} restored"

    return {
        "text": fallback_text,
        "blocks": _enforce_block_cap(blocks),
        "unfurl_links": False,
        "unfurl_media": False,
    }


def build_link_check_error_message(error: str) -> dict:
    """
    Build Slack message for link check failure.

    Args:
        error: Error message

    Returns:
        Slack message payload
    """
    return {
        "text": f"Link Check Failed: {error}",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "Link Check Failed", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f":x: *Error:* {error}"}},
        ],
    }
