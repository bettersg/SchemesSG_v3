# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "firebase-admin>=6.0.0",
#   "loguru==0.7.2",
#   "python-dotenv==1.0.1",
# ]
# ///

"""Scan Firestore schemes for URL and same-name duplicate clusters.

This script is read-only: it never updates Firestore. It writes deterministic
JSON and Markdown reports for human triage.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from firebase_admin import credentials, firestore, get_app, initialize_app
from loguru import logger


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from new_scheme.url_utils import normalize_url  # noqa: E402
from utils.scheme_lifecycle import NON_SEARCHABLE_STATUSES  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse an explicit Firebase environment and report output path."""
    parser = argparse.ArgumentParser(description="Scan schemes for duplicate URL and same-name clusters.")
    environment = parser.add_mutually_exclusive_group(required=True)
    environment.add_argument("--dev", action="store_true")
    environment.add_argument("--prod", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSON report path; a Markdown report is written beside it.",
    )
    return parser.parse_args()


def normalize_name(name: str) -> str:
    """Normalize a scheme name conservatively for human-review candidates."""
    normalized = unicodedata.normalize("NFKC", name or "").casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return " ".join(normalized.split())


def _record(doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "scheme": data.get("scheme") or data.get("Scheme") or "",
        "link": data.get("link") or data.get("Link") or "",
        "agency": data.get("agency") or data.get("Agency") or "",
        "status": data.get("status") or "active",
        "merged_into": data.get("merged_into"),
        "link_check_status_code": data.get("link_check_status_code"),
    }


def build_duplicate_report(
    schemes: list[tuple[str, dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Group equivalent URLs and normalized names without mutating input data."""
    url_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    name_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for doc_id, data in schemes:
        record = _record(doc_id, data)
        normalized_url = normalize_url(record["link"])
        if normalized_url:
            url_groups[normalized_url].append(record)

        normalized_scheme_name = normalize_name(record["scheme"])
        if normalized_scheme_name:
            name_groups[normalized_scheme_name].append(record)

    def clusters(groups: dict[str, list[dict[str, Any]]], key_name: str):
        return [
            {
                key_name: key,
                "active_candidates": sum(item["status"] not in NON_SEARCHABLE_STATUSES for item in items),
                "schemes": sorted(items, key=lambda item: item["doc_id"]),
            }
            for key, items in sorted(groups.items())
            if len(items) > 1
        ]

    return {
        "url_clusters": clusters(url_groups, "normalized_url"),
        "same_name_clusters": clusters(name_groups, "normalized_name"),
    }


def _load_firestore(use_prod: bool):
    env_name = ".env.prod" if use_prod else ".env.dev"
    load_dotenv(Path(__file__).resolve().parents[1] / env_name, override=True)
    private_key = os.getenv("FB_PRIVATE_KEY", "").replace("\\n", "\n")
    credential = credentials.Certificate(
        {
            "type": os.getenv("FB_TYPE"),
            "project_id": os.getenv("FB_PROJECT_ID"),
            "private_key_id": os.getenv("FB_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": os.getenv("FB_CLIENT_EMAIL"),
            "client_id": os.getenv("FB_CLIENT_ID"),
            "auth_uri": os.getenv("FB_AUTH_URI"),
            "token_uri": os.getenv("FB_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FB_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FB_CLIENT_X509_CERT_URL"),
        }
    )
    app_name = "production" if use_prod else "development"
    try:
        app = get_app(app_name)
    except ValueError:
        app = initialize_app(credential, name=app_name)

    expected_project_id = os.getenv("FB_PROJECT_ID")
    if app.project_id != expected_project_id:
        raise RuntimeError(
            f"Firebase app {app_name!r} targets {app.project_id!r}, "
            f"expected {expected_project_id!r}"
        )
    logger.info(f"Connected to Firebase project {app.project_id!r} using app {app.name!r}")
    return firestore.client(app=app)


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Scheme duplicate-cluster scan",
        "",
        f"Project: `{report['project_id']}`  ",
        f"Generated: `{report['generated_at']}`",
        "",
    ]
    for title, key, match_key in (
        ("Normalized URL clusters", "url_clusters", "normalized_url"),
        ("Same-name candidates", "same_name_clusters", "normalized_name"),
    ):
        clusters = report[key]
        lines.extend([f"## {title}", "", f"Clusters: **{len(clusters)}**", ""])
        for cluster in clusters:
            lines.extend([f"### `{cluster[match_key]}`", ""])
            for scheme in cluster["schemes"]:
                lines.append(f"- `{scheme['doc_id']}` — {scheme['scheme']} — {scheme['status']} — {scheme['link']}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    db = _load_firestore(args.prod)
    schemes = [(doc.id, doc.to_dict() or {}) for doc in db.collection("schemes").stream()]
    clusters = build_duplicate_report(schemes)
    report = {
        "project_id": os.getenv("FB_PROJECT_ID"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scheme_count": len(schemes),
        **clusters,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path = args.output.with_suffix(".md")
    _write_markdown(markdown_path, report)
    logger.info(f"Wrote {args.output} and {markdown_path}")


if __name__ == "__main__":
    main()
