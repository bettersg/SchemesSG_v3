
import os
import time
from typing import Any

import requests
from loguru import logger


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2025-09-03"


def to_rich_text(value: Any) -> list[dict]:
    """Convert text to Notion rich-text objects."""
    content = str(value or "")

    return [
        {
            "type": "text",
            "text": {"content": content[i:i + 2000]},
        }
        for i in range(0, len(content), 2000)
    ]


def to_url(value: str | None) -> str | None:
    if value and value.startswith(("http://", "https://")):
        return value
    return None


def create_notion_row(
    session: requests.Session,
    data_source_id: str,
    record: dict,
    max_retries: int = 3,
) -> str:
    """Create a Notion row and return its page ID."""

    properties = {
        "Scheme Name": {
            "title": to_rich_text(record["scheme_name"])
        },
        "Firestore ID": {
            "rich_text": to_rich_text(record["doc_id"])
        },
        "Previous Link": {
            "url": to_url(record.get("previous_link"))
        },
        "Discovered Link": {
            "url": to_url(record.get("discovered_url"))
        },
        "Agent Summary": {
            "rich_text": to_rich_text(record.get("summary"))
        },
        "Evidence URLs": {
            "rich_text": to_rich_text(
                "\n".join(record.get("evidence_urls") or [])
            )
        },
        "Discovery Status": {
            "select": {
                "name": record["discovery_status"]
            }
        },
        "Verification Status": {
            "select": {"name": "Pending"}
        },
    }

    payload = {
        "parent": {
            "type": "data_source_id",
            "data_source_id": data_source_id,
        },
        "properties": properties,
    }

    for attempt in range(max_retries):
        response = session.post(
            f"{NOTION_API_BASE}/pages",
            json=payload,
            timeout=30,
        )

        if response.status_code == 429:
            if attempt == max_retries - 1:
                response.raise_for_status()

            retry_after = response.headers.get("Retry-After", "1")
            try:
                delay = max(float(retry_after), 1.0)
            except ValueError:
                delay = 1.0

            time.sleep(delay)
            continue

        response.raise_for_status()
        return response.json()["id"]

    raise RuntimeError("Notion request failed after retries")


def publish_discovery_to_notion(
    found_links: list[dict],
    not_found_links: list[dict],
) -> dict[str, Any]:
    """
    Insert new discovery records into a Notion data source.

    Assumes each doc_id has already been filtered for uniqueness.
    Does not update or delete existing Notion rows.
    """

    token = os.getenv("NOTION_BROKEN_LINK_API_KEY")
    data_source_id = os.getenv("NOTION_BROKEN_LINK_DATA_SOURCE_ID")

    records = [
        {**item, "discovery_status": "Found"}
        for item in found_links
    ] + [
        {**item, "discovery_status": "Not Found"}
        for item in not_found_links
    ]

    published = []
    failed = []

    if not records:
        return {
            "total": 0,
            "published_count": 0,
            "failed_count": 0,
            "published": [],
            "failed": [],
        }

    with requests.Session() as session:
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        })

        for record in records:
            doc_id = record["doc_id"]

            try:
                notion_page_id = create_notion_row(
                    session=session,
                    data_source_id=data_source_id,
                    record=record,
                )

                published.append({
                    "doc_id": doc_id,
                    "notion_page_id": notion_page_id,
                })

                logger.info(
                    f"Published {doc_id} to Notion: "
                    f"{notion_page_id}"
                )

            except requests.RequestException as exc:
                logger.error(
                    f"Notion publishing failed for {doc_id}: {exc}"
                )
                failed.append({
                    "doc_id": doc_id,
                    "error": str(exc),
                })

            except Exception as exc:
                logger.exception(
                    f"Unexpected Notion error for {doc_id}: {exc}"
                )
                failed.append({
                    "doc_id": doc_id,
                    "error": str(exc),
                })

            # Notion's average rate limit is approximately
            # 3 requests per second per integration.
            time.sleep(0.4)

    return {
        "total": len(records),
        "published_count": len(published),
        "failed_count": len(failed),
        "published": published,
        "failed": failed,
    }
