"""
Slack Block Kit builders for link check & reindex batch job.

Builds summary messages for link health check results.
"""
from typing import Dict, Any, List


def build_link_check_summary_message(
    results: Dict[str, Any],
    dead_links: List[Dict[str, Any]],
    reindex_result: Dict[str, Any],
    restored_links: List[Dict[str, Any]] = None
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
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Link Check & Reindex Complete", "emoji": True}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary_text}
        },
    ]

    # Add restored links section if any
    if restored_links:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Restored Links ({len(restored_links)}) - previously inactive:*"}
        })

        for link in restored_links:
            doc_id = link.get("doc_id", "Unknown")
            scheme_name = link.get("scheme_name", "Unknown")
            link_url = link.get("link", "")
            previous_error = link.get("previous_error", "Unknown")

            restored_text = f"• *{scheme_name}*\n  ID: `{doc_id}`\n  Link: {link_url}\n  Previous error: _{previous_error}_"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": restored_text}
            })

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": ":recycle: Status restored to active for these schemes"}
            ]
        })

    # Add dead links section if any found
    if dead_links:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Dead Links Detected ({len(dead_links)}):*"}
        })

        # Build dead links list - each as a separate section to avoid text limits
        for link in dead_links:
            doc_id = link.get("doc_id", "Unknown")
            scheme_name = link.get("scheme_name", "Unknown")
            link_url = link.get("link", "")
            error = link.get("error", "Unknown error")

            dead_link_text = f"• *{scheme_name}*\n  ID: `{doc_id}`\n  Link: {link_url}\n  Error: _{error}_"

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": dead_link_text}
            })

        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": ":warning: Status updated to 'inactive' for all dead links"}
            ]
        })

    # Add reindex result
    blocks.append({"type": "divider"})

    if reindex_result.get("success"):
        reindex_text = (
            f":arrows_counterclockwise: *Embeddings Reindex:* Complete\n"
            f"• Schemes indexed: {reindex_result.get('indexed_schemes', 0)}\n"
            f"• Inactive skipped: {reindex_result.get('skipped_inactive', 0)}"
        )
    else:
        reindex_text = (
            f":x: *Embeddings Reindex:* Failed\n"
            f"• Error: {reindex_result.get('error', 'Unknown')}"
        )

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": reindex_text}
    })

    # Build fallback text
    fallback_text = f"Link Check Complete: {alive_count} active, {dead_count} dead"
    if restored_count > 0:
        fallback_text += f", {restored_count} restored"

    return {
        "text": fallback_text,
        "blocks": blocks,
        "unfurl_links": False,
        "unfurl_media": False
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
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Link Check Failed", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":x: *Error:* {error}"
                }
            }
        ]
    }
