"""Tests for the catalog endpoint."""

import json

from schemes.catalog import CatalogRequestParams, _handle_catalog_request, _parse_query_params, catalog
from utils.catalog_pagination import PaginationResult
from werkzeug.datastructures import MultiDict


def test_catalog_warmup_request(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint with warmup request."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET", args={"is_warmup": "true"})

    response = catalog(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert "Warmup request received" == response_data["message"]


def test_catalog_invalid_method(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint with invalid HTTP method."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="POST")

    response = catalog(request)

    assert response.status_code == 405
    response_data = json.loads(response.get_data())
    assert "Invalid request method; only GET is supported" == response_data["error"]


def test_catalog_invalid_query(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint with invalid query parameters."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET", args={"area": "TAMPINES", "scheme_type": "healthcare"})

    response = catalog(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Error parsing query parameters" in response_data["error"]


def test_catalog_successful_scheme_type_fetch(mock_request, mock_https_response, mock_auth, mocker):
    """Test successful catalog fetch with scheme_type filtering."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection.return_value = mock_collection

    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    field_filter = mocker.patch("schemes.catalog.FieldFilter", return_value="scheme-type-filter")
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[{"scheme_name": "Test Scheme", "scheme_type": ["healthcare"]}],
            next_cursor="next-page",
            has_more=True,
        ),
    )

    request = mock_request(method="GET", args={"scheme_type": "healthcare", "limit": "2"})

    response = catalog(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["data"][0]["scheme_name"] == "Test Scheme"
    assert response_data["next_cursor"] == "next-page"
    assert response_data["has_more"] is True
    mock_manager.firestore_client.collection.assert_called_once_with("schemes")
    field_filter.assert_called_once_with("scheme_type", "array_contains", "Healthcare")
    mock_collection.where.assert_called_once_with(filter="scheme-type-filter")


def test_catalog_not_found(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint when no schemes are found."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    mocker.patch("schemes.catalog.get_paginated_results", return_value=PaginationResult(data=[]))

    request = mock_request(method="GET", args={"scheme_type": "healthcare"})

    response = catalog(request)

    assert response.status_code == 404
    response_data = json.loads(response.get_data())
    assert "No scheme found" == response_data["error"]


def test_catalog_firestore_error(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint when Firestore query fails."""
    mock_collection = mocker.MagicMock()
    mock_collection.where.side_effect = Exception("Firestore error")

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection.return_value = mock_collection

    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    mocker.patch("schemes.catalog.FieldFilter", return_value="scheme-type-filter")

    request = mock_request(method="GET", args={"scheme_type": "healthcare"})

    response = catalog(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert "Internal server error" in response_data["error"]


def test_catalog_cors_preflight(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")

    response = catalog(request)

    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"


def test_parse_query_params_scheme_type():
    """Parse a scheme_type catalog request."""
    params = _parse_query_params(MultiDict([("scheme_type", "healthcare"), ("limit", "5"), ("cursor", "abc")]))

    assert isinstance(params, CatalogRequestParams)
    assert params.filter_name == "scheme_type"
    assert params.filter_value == "Healthcare"
    assert params.limit == 5
    assert params.cursor == "abc"


def test_parse_query_params_rejects_multiple_filters():
    """Reject requests that mix catalog filter types."""
    try:
        _parse_query_params(MultiDict([("area", "TAMPINES"), ("scheme_type", "healthcare")]))
        assert False, "Expected ValueError for multiple filters"
    except ValueError as exc:
        assert "'area', 'scheme_type'" in str(exc)


def test_parse_query_params_normalizes_scheme_type_casing():
    """Normalize scheme_type with mixed casing (e.g. housing/shelter)."""
    params = _parse_query_params(MultiDict([("scheme_type", "housing/shelter")]))
    assert params.filter_value == "Housing/Shelter"


def test_parse_query_params_rejects_unknown_scheme_type():
    """Reject unknown scheme_type values."""
    try:
        _parse_query_params(MultiDict([("scheme_type", "bogus")]))
        assert False, "Expected ValueError for unknown scheme_type"
    except ValueError as exc:
        assert "Unknown scheme_type" in str(exc)


def test_handle_catalog_request_uses_array_contains_for_scheme_type(mocker, mock_firebase_manager):
    """Build a Firestore array_contains query for scheme_type."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    field_filter = mocker.patch("schemes.catalog.FieldFilter", return_value="scheme-type-filter")
    get_paginated_results = mocker.patch("schemes.catalog.get_paginated_results")

    query_params = CatalogRequestParams(
        filter_name="scheme_type",
        filter_value="Healthcare",
        limit=3,
        cursor="next-page",
    )

    _handle_catalog_request(mock_firebase_manager, query_params)

    mock_firebase_manager.firestore_client.collection.assert_called_once_with("schemes")
    field_filter.assert_called_once_with("scheme_type", "array_contains", "Healthcare")
    mock_collection.where.assert_called_once_with(filter="scheme-type-filter")
    get_paginated_results.assert_called_once_with(
        collection_ref=mock_collection,
        base_query=mock_query,
        cursor="next-page",
        limit=3,
    )
