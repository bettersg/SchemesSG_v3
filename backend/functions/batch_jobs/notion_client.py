"""
Minimal Notion REST client shared by batch jobs.

Restored from the removed Notion link queue (89bf5d7) with block and trash calls added. Plain API
calls only: no Notion AI, nothing that needs a paid plan. Property names are matched by name, so
the column names in a job's schema are a contract with its Notion database.
"""

import time
from typing import Any, Dict, Iterable, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
# Notion allows ~3 requests/second per connection.
REQUEST_INTERVAL_SEC = 0.34
# Notion rejects a single rich-text piece longer than this; longer text is split into pieces.
MAX_TEXT = 2000
# ...and a rich-text value with more pieces than this.
MAX_PIECES = 100


class NotionClient:
    """The Notion REST calls our batch jobs need."""

    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )
        # Retry only 429s (never processed) and connection failures. read=0 so a
        # page-create POST that may have landed is never replayed into a duplicate row.
        retry = Retry(
            total=5,
            connect=2,
            read=0,
            status=5,
            status_forcelist=[429],
            allowed_methods=None,
            backoff_factor=1,
            raise_on_status=False,
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def _call(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        time.sleep(REQUEST_INTERVAL_SEC)
        response = self._session.request(method, f"{NOTION_API}{path}", json=body, timeout=30)
        if not response.ok:
            raise RuntimeError(f"Notion {method} {path} -> {response.status_code}: {response.text[:500]}")
        return response.json()

    def query_all(self, data_source_id: str, filter: Optional[dict] = None) -> List[dict]:
        rows: List[dict] = []
        body: Dict[str, Any] = {"page_size": 100}
        if filter:
            body["filter"] = filter
        while True:
            result = self._call("POST", f"/data_sources/{data_source_id}/query", body)
            rows.extend(result["results"])
            if not result.get("has_more"):
                return rows
            body["start_cursor"] = result["next_cursor"]

    def create_page(self, data_source_id: str, properties: dict, children: Optional[List[dict]] = None) -> dict:
        parent = {"type": "data_source_id", "data_source_id": data_source_id}
        body: Dict[str, Any] = {"parent": parent, "properties": properties}
        if children:
            body["children"] = children
        return self._call("POST", "/pages", body)

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self._call("PATCH", f"/pages/{page_id}", {"properties": properties})

    def trash_page(self, page_id: str) -> dict:
        """Move a row to Notion's trash (restorable there for ~30 days)."""
        return self._call("PATCH", f"/pages/{page_id}", {"in_trash": True})

    def replace_children(self, page_id: str, children: List[dict]) -> None:
        """Replace a page's body: delete its top-level blocks, then append `children`."""
        cursor: Optional[str] = None
        block_ids: List[str] = []
        while True:
            query = f"?page_size=100&start_cursor={cursor}" if cursor else "?page_size=100"
            result = self._call("GET", f"/blocks/{page_id}/children{query}")
            block_ids.extend(block["id"] for block in result["results"])
            if not result.get("has_more"):
                break
            cursor = result["next_cursor"]
        for block_id in block_ids:
            self._call("DELETE", f"/blocks/{block_id}")
        if children:
            self._call("PATCH", f"/blocks/{page_id}/children", {"children": children})


def rich_text(value: Any) -> List[dict]:
    """Text -> Notion rich-text pieces, split at MAX_TEXT so long text is kept whole."""
    content = str(value or "")
    pieces = [content[i : i + MAX_TEXT] for i in range(0, len(content), MAX_TEXT)][:MAX_PIECES]
    return [{"type": "text", "text": {"content": piece}} for piece in pieces]


def decode_property(prop: dict) -> Any:
    """Notion property value -> plain Python value."""
    kind = prop.get("type")
    value = prop.get(kind)
    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in value or [])
    if kind == "select":
        return value["name"] if value else None
    if kind == "multi_select":
        return [option["name"] for option in value or []]
    if kind == "date":
        return value["start"] if value else None
    if kind == "people":
        return [person.get("name") or person["id"] for person in value or []]
    if kind == "formula":
        return (value or {}).get((value or {}).get("type"))
    return value


def decode_row(page: dict) -> Dict[str, Any]:
    return {name: decode_property(prop) for name, prop in page.get("properties", {}).items()}


def encode_properties(values: Dict[str, Any], types: Dict[str, str]) -> dict:
    """Plain values -> Notion property payload."""
    encoded = {}
    for name, value in values.items():
        kind = types[name]
        if kind in ("title", "rich_text"):
            encoded[name] = {kind: rich_text(value)}
        elif kind == "select":
            encoded[name] = {"select": {"name": value} if value else None}
        elif kind == "multi_select":
            encoded[name] = {"multi_select": [{"name": option} for option in _as_list(value)]}
        elif kind == "date":
            encoded[name] = {"date": {"start": value} if value else None}
        elif kind == "url":
            encoded[name] = {"url": value[:MAX_TEXT] if value else None}
        else:
            encoded[name] = {kind: value}
    return encoded


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    items: Iterable[Any] = value if isinstance(value, (list, tuple)) else str(value).split(",")
    return [str(item).strip() for item in items if str(item).strip()]
