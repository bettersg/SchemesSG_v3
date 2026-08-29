"""Shared test fixtures and tier classification."""

from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Classify tests by directory while allowing explicit smoke markers."""
    for item in items:
        try:
            relative_path = item.path.relative_to(TEST_ROOT)
        except ValueError:
            continue

        if relative_path.parts[0] == "unit":
            item.add_marker(pytest.mark.unit)
        elif relative_path.parts[0] == "integration":
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def mock_firebase_manager(mocker):
    """Mock FirebaseManager instance."""
    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client = mocker.MagicMock()
    return mock_manager
