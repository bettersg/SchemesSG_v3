"""Catalog projection contracts for public static rendering."""

from utils.catalog_pagination import _get_paginated_query


def test_catalog_projection_keeps_routing_and_lifecycle_fields(mocker):
    """Compact catalog rows still carry fields needed to publish safe routes."""
    collection = mocker.MagicMock()
    projected = collection.select.return_value
    updated_order = projected.order_by.return_value
    stable_order = updated_order.order_by.return_value

    _get_paginated_query(collection, limit=20)

    selected_fields = set(collection.select.call_args.args)
    assert {"scheme", "scheme_type", "status", "merged_into"} <= selected_fields
    assert "scraped_text" not in selected_fields
    projected.order_by.assert_called_once_with("last_scraped_update", direction="DESCENDING")
    updated_order.order_by.assert_called_once_with("__name__", direction="ASCENDING")
    stable_order.limit.assert_called_once_with(21)
