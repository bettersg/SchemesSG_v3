"""Shared test fixtures for both unit and integration tests."""

import pytest


@pytest.fixture
def mock_firebase_manager(mocker):
    """Mock FirebaseManager instance."""
    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client = mocker.MagicMock()
    return mock_manager
