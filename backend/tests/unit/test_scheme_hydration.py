"""Contracts for batch hydration shared by search and scheme-detail tools."""

from types import SimpleNamespace

import pytest
from search.retriever import fetch_schemes_by_ids


def snapshot(scheme_id, data):
    return SimpleNamespace(
        id=scheme_id,
        exists=data is not None,
        to_dict=lambda: dict(data) if data is not None else None,
    )


def manager_with_documents(mocker, documents):
    db = mocker.MagicMock()
    refs = {doc.id: mocker.MagicMock(id=doc.id) for doc in documents}
    for doc in documents:
        refs[doc.id].get.return_value = doc
    db.collection.return_value.document.side_effect = refs.__getitem__
    db.get_all.return_value = iter(reversed(documents))
    return SimpleNamespace(firestore_client=db), refs


def test_batch_preserves_order_normalization_lifecycle_and_fields(mocker):
    manager, refs = manager_with_documents(mocker, [
        snapshot("a", {"scheme": "A", "status": "active", "scraped_text": "large"}),
        snapshot("b", {"scheme": "B", "status": "inactive"}),
        snapshot("retired", {"status": "retired"}),
        snapshot("missing", None),
    ])

    schemes, missing = fetch_schemes_by_ids(manager, [" b ", "", "a", "b", "retired", "missing", " "])

    assert schemes == [
        {"scheme": "B", "status": "inactive", "scheme_id": "b"},
        {"scheme": "A", "status": "active", "scheme_id": "a"},
    ]
    assert missing == ["retired", "missing"]
    manager.firestore_client.get_all.assert_called_once_with([refs[key] for key in ("b", "a", "retired", "missing")])
    for ref in refs.values():
        ref.get.assert_not_called()


@pytest.mark.parametrize("ids", [[], ["", " "]])
def test_empty_input_avoids_database_requests(mocker, ids):
    manager, _ = manager_with_documents(mocker, [])
    assert fetch_schemes_by_ids(manager, ids) == ([], [])
    manager.firestore_client.get_all.assert_not_called()
    manager.firestore_client.collection.assert_not_called()


def test_large_candidate_pool_uses_one_batch(mocker):
    ids = [f"s{i}" for i in range(1000)]
    manager, refs = manager_with_documents(mocker, [snapshot(key, {"scheme": key}) for key in ids])

    schemes, missing = fetch_schemes_by_ids(manager, ids)

    assert [scheme["scheme_id"] for scheme in schemes] == ids
    assert missing == []
    manager.firestore_client.get_all.assert_called_once_with([refs[key] for key in ids])
    assert all(not ref.get.called for ref in refs.values())


def test_batch_failure_does_not_return_partial_results(mocker):
    doc = snapshot("a", {"scheme": "A"})
    manager, _ = manager_with_documents(mocker, [doc])

    def failing_stream():
        yield doc
        raise RuntimeError("batch interrupted")

    manager.firestore_client.get_all.return_value = failing_stream()
    with pytest.raises(RuntimeError, match="batch interrupted"):
        fetch_schemes_by_ids(manager, ["a"])


def test_detail_tool_keeps_order_and_reports_unavailable_ids(mocker):
    from agent.tools.retrieve_scheme import retrieve_schemes_by_ids

    manager, _ = manager_with_documents(mocker, [
        snapshot("a", {"scheme": "A"}),
        snapshot("b", {"scheme": "B"}),
        snapshot("missing", None),
        snapshot("retired", {"status": "retired"}),
    ])
    mocker.patch("agent.tools.retrieve_scheme.FirebaseManager", return_value=manager)

    result = retrieve_schemes_by_ids(["b", "a", "missing", "retired"])

    assert [scheme["scheme_id"] for scheme in result["schemes"]] == ["b", "a"]
    assert result["missing_scheme_ids"] == ["missing", "retired"]
    assert result["result_count"] == 2
