"""Catalog projection contracts for public static rendering."""

from utils.catalog_pagination import _count_total, _get_paginated_query


def test_catalog_projection_keeps_routing_and_lifecycle_fields(mocker):
    """Compact catalog rows still carry fields needed to publish safe routes."""
    collection = mocker.MagicMock()
    projected = collection.select.return_value
    updated_order = projected.order_by.return_value

    _get_paginated_query(collection, limit=20)

    selected_fields = set(collection.select.call_args.args)
    assert {"scheme", "scheme_type", "status", "merged_into"} <= selected_fields
    assert "scraped_text" not in selected_fields
    projected.order_by.assert_called_once_with("last_scraped_update", direction="DESCENDING")
    updated_order.limit.assert_called_once_with(21)


def test_catalog_query_leaves_the_document_tie_break_implicit(mocker):
    """An explicit `__name__` order would need composite indexes we do not deploy."""
    collection = mocker.MagicMock()
    updated_order = collection.select.return_value.order_by.return_value

    _get_paginated_query(collection, limit=20)

    updated_order.order_by.assert_not_called()


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
