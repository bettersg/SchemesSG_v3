"""Unit tests for new_scheme.url_utils."""

from unittest.mock import MagicMock

import pytest

from new_scheme.url_utils import check_duplicate_scheme, normalize_url


def test_normalize_url_strips_www_and_trailing_slash():
    assert normalize_url("https://www.example.com/foo/") == "example.com/foo"


def test_normalize_url_strips_query_and_fragment():
    assert normalize_url("https://Example.com/foo?ref=1#x") == "example.com/foo"


def test_check_duplicate_scheme_finds_match(mocker):
    doc_a = MagicMock()
    doc_a.id = "scheme-a"
    doc_a.to_dict.return_value = {
        "link": "https://www.example.com/foo",
        "scheme": "Alpha",
    }

    client = MagicMock()
    client.collection.return_value.stream.return_value = [doc_a]
    mocker.patch("new_scheme.url_utils.firestore.client", return_value=client)

    result = check_duplicate_scheme("https://example.com/foo/")
    assert result is not None
    assert result["doc_id"] == "scheme-a"
    assert result["scheme"] == "Alpha"


def test_check_duplicate_scheme_excludes_target(mocker):
    doc_a = MagicMock()
    doc_a.id = "scheme-a"
    doc_a.to_dict.return_value = {"link": "https://www.example.com/foo"}

    client = MagicMock()
    client.collection.return_value.stream.return_value = [doc_a]
    mocker.patch("new_scheme.url_utils.firestore.client", return_value=client)

    result = check_duplicate_scheme(
        "https://example.com/foo/", exclude_doc_id="scheme-a"
    )
    assert result is None


def test_check_duplicate_scheme_excludes_target_but_finds_other(mocker):
    doc_a = MagicMock()
    doc_a.id = "scheme-a"
    doc_a.to_dict.return_value = {"link": "https://example.com/foo", "scheme": "A"}

    doc_b = MagicMock()
    doc_b.id = "scheme-b"
    doc_b.to_dict.return_value = {"link": "https://example.com/foo", "scheme": "B"}

    client = MagicMock()
    client.collection.return_value.stream.return_value = [doc_a, doc_b]
    mocker.patch("new_scheme.url_utils.firestore.client", return_value=client)

    result = check_duplicate_scheme(
        "https://example.com/foo/", exclude_doc_id="scheme-a"
    )
    assert result is not None
    assert result["doc_id"] == "scheme-b"


def test_check_duplicate_scheme_no_match(mocker):
    doc = MagicMock()
    doc.id = "other"
    doc.to_dict.return_value = {"link": "https://nope.com/x"}

    client = MagicMock()
    client.collection.return_value.stream.return_value = [doc]
    mocker.patch("new_scheme.url_utils.firestore.client", return_value=client)

    assert check_duplicate_scheme("https://example.com/foo/") is None
