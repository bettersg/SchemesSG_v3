"""firestore_peek: read-only lookups print trimmed JSON lines, filter on create time and never write."""

import json
from datetime import datetime, timezone

import pytest

from scripts import firestore_peek as fp


class Snap:
    def __init__(self, doc_id, data, created):
        self.id, self._data, self.exists, self.create_time = doc_id, data, True, created

    def to_dict(self):
        return dict(self._data)


class FakeQuery:
    """Collection/query stand-in that records filters and fails on any write call."""

    def __init__(self, snaps):
        self.snaps, self.filters, self.selected = snaps, [], None

    def where(self, filter):
        self.filters.append((filter.field_path, filter.value))
        return self

    def select(self, fields):
        self.selected = fields
        return self

    def stream(self):
        return iter(self.snaps)

    def document(self, doc_id):
        query = self

        class Doc:
            def get(self, field_paths=None):
                query.selected = field_paths
                return next(s for s in query.snaps if s.id == doc_id)

        return Doc()


EARLY = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
LATE = datetime(2026, 11, 1, 13, 0, tzinfo=timezone.utc)


@pytest.fixture
def peek(monkeypatch, capsys):
    def _peek(snaps, *argv):
        query = FakeQuery(snaps)
        monkeypatch.setattr(fp, "load_environment", lambda env: env)
        monkeypatch.setattr(
            fp, "firestore_client", lambda _name: type("Db", (), {"collection": lambda self, n: query})()
        )
        fp.main(list(argv))
        lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
        return query, lines

    return _peek


def test_where_values_parse_as_json_when_they_can():
    assert fp.parse_where("pipeline_status=failed") == ("pipeline_status", "failed")
    assert fp.parse_where("active=true") == ("active", True)
    with pytest.raises(SystemExit):
        fp.parse_where("no-equals-sign")


def test_since_reads_z_and_naive_times_as_utc():
    assert fp.parse_since("2026-11-01T12:30:00Z") == datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc)
    assert fp.parse_since("2026-11-01") == datetime(2026, 11, 1, tzinfo=timezone.utc)


def test_query_selects_fields_filters_and_keeps_only_recent_docs(peek):
    snaps = [Snap("old", {"Scheme": "A"}, EARLY), Snap("new", {"Scheme": "B"}, LATE)]
    query, lines = peek(
        snaps,
        "prod",
        "schemeEntries",
        "--where",
        "pipeline_status=failed",
        "--since",
        "2026-11-01T12:30:00Z",
        "--fields",
        "Scheme",
    )
    assert query.filters == [("pipeline_status", "failed")]
    assert query.selected == ["Scheme"]
    assert [line["_id"] for line in lines] == ["new"]


def test_default_output_drops_bulky_fields_and_cuts_long_strings(peek):
    snaps = [Snap("x", {"scheme": "S", "scraped_text": "<html>", "summary": "y" * 50}, LATE)]
    _, [line] = peek(snaps, "dev", "schemes", "x", "--max-chars", "10")
    assert "scraped_text" not in line
    assert line["summary"].startswith("yyyyyyyyyy…")


def test_dotted_fields_read_nested_values(peek):
    snaps = [Snap("x", {"llm_fields": {"scheme_type": ["Caregiver Support"]}}, LATE)]
    _, [line] = peek(snaps, "prod", "schemeEntries", "x", "--fields", "llm_fields.scheme_type,llm_fields.missing")
    assert line["llm_fields.scheme_type"] == ["Caregiver Support"]
    assert line["llm_fields.missing"] is None


def test_count_prints_only_the_number(peek):
    snaps = [Snap(str(i), {}, LATE) for i in range(3)]
    _, lines = peek(snaps, "dev", "schemes", "--count")
    assert lines == []
