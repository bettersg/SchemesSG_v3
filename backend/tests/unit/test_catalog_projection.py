"""Catalog projection contracts for public static rendering."""

from google.cloud.firestore_v1 import CollectionReference
from google.cloud.firestore_v1.base_query import BaseQuery

from utils.catalog_pagination import _count_total, _get_paginated_query


def _query_chain(mocker):
    """Signature-enforcing stand-ins for the Firestore query chain.

    A bare `MagicMock` accepts any call shape, which is how `select(*fields)` —
    fourteen positional arguments to a method taking one iterable — passed its
    unit test and then raised `TypeError` on every deployed catalog read.
    Autospec makes the real signatures binding.
    """
    collection = mocker.create_autospec(CollectionReference, instance=True)
    projected = mocker.create_autospec(BaseQuery, instance=True)
    ordered = mocker.create_autospec(BaseQuery, instance=True)
    collection.select.return_value = projected
    projected.order_by.return_value = ordered
    return collection, projected, ordered


def test_catalog_projection_keeps_routing_and_lifecycle_fields(mocker):
    """Compact catalog rows still carry fields needed to publish safe routes."""
    collection, projected, ordered = _query_chain(mocker)

    _get_paginated_query(collection, limit=20)

    (field_paths,) = collection.select.call_args.args
    selected_fields = set(field_paths)
    assert {"scheme", "scheme_type", "status", "merged_into"} <= selected_fields
    assert "scraped_text" not in selected_fields
    projected.order_by.assert_called_once_with("last_scraped_update", direction="DESCENDING")
    ordered.limit.assert_called_once_with(21)


def test_catalog_projection_passes_one_iterable_of_field_paths(mocker):
    """`select()` takes `field_paths: Iterable[str]`, so splatting raises TypeError."""
    collection, _, _ = _query_chain(mocker)

    _get_paginated_query(collection, limit=20)

    assert len(collection.select.call_args.args) == 1
    assert not collection.select.call_args.kwargs


def test_catalog_query_leaves_the_document_tie_break_implicit(mocker):
    """An explicit `__name__` order would need composite indexes we do not deploy."""
    collection, _, ordered = _query_chain(mocker)

    _get_paginated_query(collection, limit=20)

    ordered.order_by.assert_not_called()


def test_catalog_total_count_issues_no_order_by(mocker):
    """Ordering the count would need a composite index per filter combination."""
    collection = mocker.MagicMock()
    collection.count.return_value.get.return_value = [[mocker.MagicMock(value=7)]]

    assert _count_total(collection) == 7

    collection.order_by.assert_not_called()


def test_catalog_status_count_issues_no_order_by(mocker):
    """`_count_excluded_schemes` counts a `status ==` filter through here.

    Ordering it needs `(status, last_scraped_update)` — and, under a category or
    agency filter, a three-field index. None are deployed, so every catalog read
    returned 500 the last time this count carried an `order_by`.
    """
    collection = mocker.MagicMock()
    status_filter = collection.where.return_value
    status_filter.count.return_value.get.return_value = [[mocker.MagicMock(value=3)]]

    assert _count_total(collection, status_filter) == 3

    status_filter.order_by.assert_not_called()
