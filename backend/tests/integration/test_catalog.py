"""Tests for the catalog endpoint."""

import json
from collections import Counter

from new_scheme.constants import SCHEME_CATEGORY_MAPPING, SCHEME_TYPE
from schemes.catalog import (
    CatalogRequestParams,
    _handle_catalog_request,
    _parse_query_params,
    catalog,
)
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
    """Test catalog endpoint with multiple filters supplied together."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)

    request = mock_request(
        method="GET", args={"area": "TAMPINES", "category": "health & wellbeing"}
    )

    response = catalog(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Error parsing query parameters" in response_data["error"]


def test_catalog_successful_category_fetch(
    mock_request, mock_https_response, mock_auth, mocker
):
    """Test successful catalog fetch with category filtering."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection.return_value = mock_collection

    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    field_filter = mocker.patch(
        "schemes.catalog.FieldFilter", return_value="category-filter"
    )
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[{"scheme_name": "Test Scheme", "scheme_type": ["Healthcare"]}],
            next_cursor="next-page",
            has_more=True,
        ),
    )

    request = mock_request(
        method="GET", args={"category": "health & wellbeing", "limit": "2"}
    )

    response = catalog(request)

    assert response.status_code == 200
    response_data = json.loads(response.get_data())
    assert response_data["data"][0]["scheme_name"] == "Test Scheme"
    assert response_data["next_cursor"] == "next-page"
    assert response_data["has_more"] is True
    mock_manager.firestore_client.collection.assert_called_once_with("schemes")
    field_filter.assert_called_once_with(
        "scheme_type",
        "array_contains_any",
        [
            "Healthcare",
            "Mental Health",
            "End-of-Life/Palliative Care",
            "Counselling and Emotional Support",
        ],
    )
    mock_collection.where.assert_called_once_with(filter="category-filter")


def test_catalog_not_found(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint when no schemes are found."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    mocker.patch(
        "schemes.catalog.get_paginated_results", return_value=PaginationResult(data=[])
    )

    request = mock_request(method="GET", args={"category": "health & wellbeing"})

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
    mocker.patch("schemes.catalog.FieldFilter", return_value="category-filter")

    request = mock_request(method="GET", args={"category": "health & wellbeing"})

    response = catalog(request)

    assert response.status_code == 500
    response_data = json.loads(response.get_data())
    assert "Internal server error" in response_data["error"]


def test_catalog_cors_preflight(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint CORS preflight request."""
    request = mock_request(method="OPTIONS")

    response = catalog(request)

    assert response.status_code == 204
    assert (
        response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    )


def test_parse_query_params_category():
    """Parse a category catalog request."""
    params = _parse_query_params(
        MultiDict(
            [("category", "health & wellbeing"), ("limit", "5"), ("cursor", "abc")]
        )
    )

    assert isinstance(params, CatalogRequestParams)
    assert params.filter_name == "category"
    assert params.filter_value == [
        "Healthcare",
        "Mental Health",
        "End-of-Life/Palliative Care",
        "Counselling and Emotional Support",
    ]
    assert params.limit == 5
    assert params.cursor == "abc"


def test_parse_query_params_rejects_multiple_filters():
    """Reject requests that mix catalog filter types."""
    try:
        _parse_query_params(
            MultiDict([("area", "TAMPINES"), ("category", "health & wellbeing")])
        )
        assert False, "Expected ValueError for multiple filters"
    except ValueError as exc:
        assert "'area', 'category'" in str(exc)


def test_parse_query_params_category_lookup_is_case_insensitive():
    """Category lookup accepts any casing from the client."""
    params = _parse_query_params(MultiDict([("category", "HEALTH & WELLBEING")]))
    assert params.filter_value == [
        "Healthcare",
        "Mental Health",
        "End-of-Life/Palliative Care",
        "Counselling and Emotional Support",
    ]


def test_category_mapping_covers_each_scheme_type_once():
    """Every raw scheme_type is assigned to exactly one public category."""
    mapped_types = [
        scheme_type
        for values in SCHEME_CATEGORY_MAPPING.values()
        for scheme_type in values
    ]

    assert set(mapped_types) == set(SCHEME_TYPE)
    assert Counter(mapped_types) == Counter(SCHEME_TYPE)


def test_category_mapping_has_no_duplicate_scheme_types():
    """No raw scheme_type appears in more than one public category."""
    mapped_types = [
        scheme_type
        for values in SCHEME_CATEGORY_MAPPING.values()
        for scheme_type in values
    ]
    duplicate_types = [
        scheme_type for scheme_type, count in Counter(mapped_types).items() if count > 1
    ]

    assert duplicate_types == []


def test_parse_query_params_rejects_unknown_category():
    """Reject unknown category values."""
    try:
        _parse_query_params(MultiDict([("category", "bogus")]))
        assert False, "Expected ValueError for unknown category"
    except ValueError as exc:
        assert "Unknown category" in str(exc)


def test_handle_catalog_request_uses_array_contains_any_for_category(
    mocker, mock_firebase_manager
):
    """Build a Firestore array_contains_any query for category."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    field_filter = mocker.patch(
        "schemes.catalog.FieldFilter", return_value="category-filter"
    )
    get_paginated_results = mocker.patch("schemes.catalog.get_paginated_results")

    query_params = CatalogRequestParams(
        filter_name="category",
        filter_value=[
            "Healthcare",
            "Mental Health",
            "End-of-Life/Palliative Care",
            "Counselling and Emotional Support",
        ],
        limit=3,
        cursor="next-page",
    )

    _handle_catalog_request(mock_firebase_manager, query_params)

    mock_firebase_manager.firestore_client.collection.assert_called_once_with("schemes")
    field_filter.assert_called_once_with(
        "scheme_type",
        "array_contains_any",
        [
            "Healthcare",
            "Mental Health",
            "End-of-Life/Palliative Care",
            "Counselling and Emotional Support",
        ],
    )
    mock_collection.where.assert_called_once_with(filter="category-filter")
    get_paginated_results.assert_called_once_with(
        collection_ref=mock_collection,
        base_query=mock_query,
        cursor="next-page",
        limit=3,
    )
