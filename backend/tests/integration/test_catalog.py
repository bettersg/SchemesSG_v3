"""Tests for the catalog endpoint."""

import json
from collections import Counter
from types import SimpleNamespace

import pytest
from new_scheme.constants import LEGACY_CATEGORY_TERMS, SCHEME_CATEGORY_MAPPING, SCHEME_TYPE
from schemes.catalog import (
    CatalogRequestParams,
    _handle_catalog_request,
    _parse_query_params,
    catalog,
)
from utils.catalog_filtering import CatalogFilters
from utils.catalog_pagination import CATALOG_FIELDS, PaginationResult
from werkzeug.datastructures import MultiDict


# v2 terms (SCHEME_CATEGORY_MAPPING) first, then pre-v2 terms still carried by un-migrated schemes
_HEALTH_CATEGORY_TERMS = [
    *SCHEME_CATEGORY_MAPPING["Health & Wellbeing"],
    *LEGACY_CATEGORY_TERMS["Health & Wellbeing"],
]

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
    """An invalid value is still a 400 when it is combined with a valid filter."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)

    request = mock_request(method="GET", args={"area": "TAMPINES", "category": "bogus"})

    response = catalog(request)

    assert response.status_code == 400
    response_data = json.loads(response.get_data())
    assert "Error parsing query parameters" in response_data["error"]


def test_catalog_successful_category_fetch(mock_request, mock_https_response, mock_auth, mocker):
    """Public catalog reads do not require a Firebase bearer token."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query
    mock_query.where.return_value.count.return_value.get.return_value = [[SimpleNamespace(value=1)]]

    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client.collection.return_value = mock_collection

    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    mocker.patch("schemes.catalog.FieldFilter", return_value="category-filter")
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[
                {
                    "scheme_name": "Test Scheme",
                    "scheme_type": ["Children", "Caregiver Support"],
                },
                {
                    "scheme_name": "Second Scheme",
                    "scheme_type": ["Caregiver Support"],
                },
            ],
            next_cursor="next-page",
            has_more=True,
            total_count=7,
        ),
    )

    request = mock_request(
        method="GET",
        headers={"Origin": "http://localhost:3000"},
        args={"category": "seniors & caregiving", "limit": "2"},
    )

    response = catalog(request)

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert json.loads(response.get_data()) == {
        "data": [
            {"scheme_name": "Test Scheme", "scheme_type": ["Caregiver Support"]},
            {"scheme_name": "Second Scheme", "scheme_type": ["Caregiver Support"]},
        ],
        "next_cursor": "next-page",
        "has_more": True,
        "total_count": 5,  # 7 minus one inactive and one retired
    }
    mock_auth.assert_not_called()


def test_catalog_not_found(mock_request, mock_https_response, mock_auth, mocker):
    """Test catalog endpoint when no schemes are found."""
    mock_manager = mocker.MagicMock()
    mocker.patch("schemes.catalog.create_firebase_manager", return_value=mock_manager)
    mocker.patch("schemes.catalog.get_paginated_results", return_value=PaginationResult(data=[]))

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
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"


def test_parse_query_params_category():
    """Parse a category catalog request."""
    params = _parse_query_params(MultiDict([("category", "health & wellbeing"), ("limit", "5"), ("cursor", "abc")]))

    assert isinstance(params, CatalogRequestParams)
    assert params.filters == {"category": _HEALTH_CATEGORY_TERMS}
    assert params.limit == 5
    assert params.cursor == "abc"


def test_parse_query_params_accepts_combined_and_repeated_filters():
    """Filters combine, and a repeated parameter carries several values (#484)."""
    params = _parse_query_params(
        MultiDict(
            [
                ("area", "tampines"),
                ("area", "Bedok"),
                ("category", "health & wellbeing"),
                ("category", "Education"),
            ]
        )
    )

    assert params.filters["area"] == ["TAMPINES", "BEDOK"]
    assert params.filters["category"] == [
        *_HEALTH_CATEGORY_TERMS,
        *SCHEME_CATEGORY_MAPPING["Education"],
        *LEGACY_CATEGORY_TERMS.get("Education", []),
    ]


def test_parse_query_params_rejects_an_empty_filter_value():
    with pytest.raises(ValueError, match="'area' must be a non-empty value"):
        _parse_query_params(MultiDict([("area", " ")]))


def test_parse_query_params_category_lookup_is_case_insensitive():
    """Category lookup accepts any casing from the client."""
    params = _parse_query_params(MultiDict([("category", "HEALTH & WELLBEING")]))
    assert params.filters["category"] == _HEALTH_CATEGORY_TERMS


def test_category_mapping_covers_each_scheme_type_once():
    """Every raw scheme_type is assigned to exactly one public category."""
    mapped_types = [scheme_type for values in SCHEME_CATEGORY_MAPPING.values() for scheme_type in values]

    assert set(mapped_types) == set(SCHEME_TYPE)
    assert Counter(mapped_types) == Counter(SCHEME_TYPE)


def test_category_mapping_has_no_duplicate_scheme_types():
    """No raw scheme_type appears in more than one public category."""
    mapped_types = [scheme_type for values in SCHEME_CATEGORY_MAPPING.values() for scheme_type in values]
    duplicate_types = [scheme_type for scheme_type, count in Counter(mapped_types).items() if count > 1]

    assert duplicate_types == []


def test_parse_query_params_rejects_unknown_category():
    """Reject unknown category values."""
    try:
        _parse_query_params(MultiDict([("category", "bogus")]))
        assert False, "Expected ValueError for unknown category"
    except ValueError as exc:
        assert "Unknown category" in str(exc)


def test_handle_catalog_request_uses_array_contains_any_for_category(mocker, mock_firebase_manager):
    """Build a Firestore array_contains_any query for category."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    field_filter = mocker.patch("schemes.catalog.FieldFilter", return_value="category-filter")
    get_paginated_results = mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[
                {
                    "scheme_name": "Test Scheme",
                    "scheme_type": ["Children", "Caregiver Support"],
                }
            ],
            next_cursor="next-page",
            has_more=True,
        ),
    )

    query_params = CatalogRequestParams(
        filters={"category": ["Elderly", "Caregiver Support"]},
        limit=1,
        cursor="next-page",
    )

    results = _handle_catalog_request(mock_firebase_manager, query_params)

    mock_firebase_manager.firestore_client.collection.assert_called_once_with("schemes")
    field_filter.assert_called_once_with(
        "scheme_type",
        "array_contains_any",
        ["Elderly", "Caregiver Support"],
    )
    mock_collection.where.assert_called_once_with(filter="category-filter")
    get_paginated_results.assert_called_once_with(
        collection_ref=mock_collection,
        base_query=mock_query,
        cursor="next-page",
        limit=1,
        fields=CATALOG_FIELDS,
    )
    assert results.data == [{"scheme_name": "Test Scheme", "scheme_type": ["Caregiver Support"]}]
    assert results.next_cursor is None
    assert results.has_more is False


def test_handle_catalog_request_preserves_scheme_types_for_area_filter(mocker, mock_firebase_manager):
    """Area goes through the in-memory path (planning_area is a string or a list), and is not trimmed."""
    mock_collection = mocker.MagicMock()
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection

    get_filtered_results = mocker.patch(
        "schemes.catalog.get_filtered_results",
        return_value=PaginationResult(
            data=[{"scheme_name": "Test Scheme", "scheme_type": ["Children", "Caregiver Support"]}],
            next_cursor="next-page",
            has_more=True,
            total_count=3,
        ),
    )

    results = _handle_catalog_request(
        mock_firebase_manager,
        CatalogRequestParams(filters={"area": ["TAMPINES"]}, limit=1, cursor="next-page"),
    )

    filters = get_filtered_results.call_args.args[1]
    assert filters == CatalogFilters(area=("TAMPINES",))
    assert get_filtered_results.call_args.kwargs["cursor"] == "next-page"
    assert results.data == [{"scheme_name": "Test Scheme", "scheme_type": ["Children", "Caregiver Support"]}]
    assert results.next_cursor == "next-page"


def test_handle_catalog_request_trims_scheme_types_for_combined_category_filter(mocker, mock_firebase_manager):
    """Category plus area: in-memory path, and the website still sees only the matched scheme types."""
    mock_firebase_manager.firestore_client.collection.return_value = mocker.MagicMock()
    get_filtered_results = mocker.patch(
        "schemes.catalog.get_filtered_results",
        return_value=PaginationResult(
            data=[{"scheme_name": "Test Scheme", "scheme_type": ["Children", "Caregiver Support"]}],
            total_count=1,
        ),
    )

    results = _handle_catalog_request(
        mock_firebase_manager,
        CatalogRequestParams(filters={"area": ["BEDOK"], "category": ["Caregiver Support"]}),
    )

    assert get_filtered_results.call_args.args[1] == CatalogFilters(
        area=("BEDOK",), scheme_types=("Caregiver Support",)
    )
    assert results.data == [{"scheme_name": "Test Scheme", "scheme_type": ["Caregiver Support"]}]


def test_handle_catalog_request_resolves_agency_spellings(mocker, mock_firebase_manager):
    """`.title()` used to turn PAVE into Pave, so 220 of 425 agencies matched nothing (#484)."""
    mock_collection = mocker.MagicMock()
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection
    mocker.patch(
        "schemes.catalog.known_agencies",
        return_value=["PAVE", "TOUCH Community Services", "Touch Community Services", "Ministry of Health (MOH)"],
    )
    field_filter = mocker.patch("schemes.catalog.FieldFilter", return_value="agency-filter")
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(data=[{"scheme_name": "Hit", "agency": "TOUCH Community Services"}]),
    )
    mocker.patch("schemes.catalog._count_excluded_schemes", return_value=0)

    _handle_catalog_request(mock_firebase_manager, CatalogRequestParams(filters={"agency": ["touch community services"]}))

    field_filter.assert_called_once_with(
        "agency", "in", ["TOUCH Community Services", "Touch Community Services"]
    )


def test_legacy_scheme_types_still_resolve_to_their_category():
    """Un-migrated schemes keep pre-v2 terms (e.g. 'Low Income'); category filters must still reach them."""
    params = _parse_query_params(MultiDict([("category", "Financial Assistance")]))

    assert "Low Income" in params.filters["category"]
    assert set(LEGACY_CATEGORY_TERMS["Financial Assistance"]) <= set(params.filters["category"])
    assert len(params.filters["category"]) <= 30  # Firestore array-contains-any limit


def test_legacy_category_terms_do_not_overlap_the_current_vocabulary():
    legacy = {t for terms in LEGACY_CATEGORY_TERMS.values() for t in terms}

    assert not legacy & set(SCHEME_TYPE)


@pytest.mark.parametrize("filters", [{}, {"category": ["Elderly"]}])
def test_handle_catalog_request_hides_inactive_and_retired_schemes(filters, mocker, mock_firebase_manager):
    """The catalog lists only searchable schemes, and its total count agrees."""
    mock_collection = mocker.MagicMock()
    mock_query = mocker.MagicMock()
    mock_collection.where.return_value = mock_query
    mock_firebase_manager.firestore_client.collection.return_value = mock_collection
    mocker.patch("schemes.catalog.FieldFilter", return_value="filter")
    mocker.patch(
        "schemes.catalog.get_paginated_results",
        return_value=PaginationResult(
            data=[
                {"scheme_name": "Active", "status": "active"},
                {"scheme_name": "Legacy"},
                {"scheme_name": "Dead link", "status": "inactive"},
                {"scheme_name": "Ended", "status": "retired"},
            ],
            has_more=False,
            total_count=10,
        ),
    )
    mocker.patch("schemes.catalog._count_total", return_value=3)  # per hidden status

    results = _handle_catalog_request(
        mock_firebase_manager,
        CatalogRequestParams(filters=filters, limit=10),
    )

    assert [item["scheme_name"] for item in results.data] == ["Active", "Legacy"]
    assert results.total_count == 10 - 3 - 3  # inactive and retired both subtracted
