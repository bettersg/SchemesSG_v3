"""Unit tests for pagination utilities."""

from utils.pagination import decode_cursor, encode_cursor, get_paginated_results


def test_cursor_encoding_decoding():
    """Test that cursor encoding and decoding works properly."""
    # Encode a cursor
    scheme_id = "test-scheme-123"
    similarity_score = 0.95
    session_id = "test-session-id"

    # Encode the cursor
    cursor = encode_cursor(scheme_id, similarity_score, session_id)

    # Verify it's a non-empty string
    assert isinstance(cursor, str)
    assert cursor

    # Decode the cursor
    decoded = decode_cursor(cursor)

    # Verify the decoded data matches what was encoded
    assert decoded is not None
    assert decoded["scheme_id"] == scheme_id
    assert decoded["similarity_score"] == similarity_score
    assert decoded["session_id"] == session_id


def test_invalid_cursor_decoding():
    """Test that invalid cursors return None when decoded."""
    # Test with invalid base64
    assert decode_cursor("not-valid-base64") is None

    # Test with empty string
    assert decode_cursor("") is None

    # Test with valid base64 but invalid structure
    assert decode_cursor("e30=") is None  # Base64 of "{}"


def test_get_paginated_results_empty():
    """Test pagination with empty results."""
    results = []

    page_results, next_cursor, has_more, total_count = get_paginated_results(results, limit=10, cursor=None)

    assert page_results == []
    assert next_cursor is None
    assert has_more is False
    assert total_count == 0


def test_get_paginated_results_single_page():
    """Test pagination with a single page of results."""
    # Create test data
    results = [{"id": f"scheme-{i}", "scheme_id": f"scheme-{i}", "combined_scores": 1.0 - (i * 0.1)} for i in range(5)]

    # Get the first page (should include all results)
    page_results, next_cursor, has_more, total_count = get_paginated_results(results, limit=10, cursor=None)

    assert len(page_results) == 5
    assert next_cursor is None
    assert has_more is False
    assert total_count == 5


def test_get_paginated_results_multiple_pages():
    """Test pagination with multiple pages of results."""
    # Create test data
    results = [
        {"id": f"scheme-{i}", "scheme_id": f"scheme-{i}", "combined_scores": 1.0 - (i * 0.1)} for i in range(25)
    ]

    # Get the first page
    limit = 10
    page1_results, page1_cursor, has_more1, total_count1 = get_paginated_results(
        results, limit=limit, cursor=None, session_id="test-session"
    )

    assert len(page1_results) == limit
    assert page1_cursor is not None
    assert has_more1 is True
    assert total_count1 == 25

    # Get the second page
    page2_results, page2_cursor, has_more2, total_count2 = get_paginated_results(
        results, limit=limit, cursor=page1_cursor, session_id="test-session"
    )

    assert len(page2_results) == limit
    assert page2_cursor is not None
    assert has_more2 is True
    assert total_count2 == 25

    # Get the third page (should be the last)
    page3_results, page3_cursor, has_more3, total_count3 = get_paginated_results(
        results, limit=limit, cursor=page2_cursor, session_id="test-session"
    )

    assert len(page3_results) == 5  # Only 5 items left
    assert page3_cursor is None
    assert has_more3 is False
    assert total_count3 == 25

    # Verify all results were included and in the correct order
    all_results = page1_results + page2_results + page3_results
    assert len(all_results) == 25

    # Verify the results are in the correct order (sorted by similarity score)
    for i in range(24):
        assert all_results[i]["combined_scores"] >= all_results[i + 1]["combined_scores"]
