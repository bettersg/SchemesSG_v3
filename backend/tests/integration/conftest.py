"""Test fixtures specific to integration tests."""

import pytest
from firebase_functions import https_fn


@pytest.fixture
def mock_request():
    """Mock Firebase Functions request object."""

    class MockRequest:
        def __init__(self, method="GET", json_data=None, headers=None):
            self.method = method
            self._json = json_data or {}
            self.headers = headers or {}

        def get_json(self, silent=False):
            return self._json

    return MockRequest


@pytest.fixture
def mock_firebase_manager(mocker):
    """Mock FirebaseManager instance."""
    mock_manager = mocker.MagicMock()
    mock_manager.firestore_client = mocker.MagicMock()
    return mock_manager


@pytest.fixture
def mock_https_response():
    """Mock Firebase Functions response object."""

    def _create_response(data, status=200, headers=None):
        response = https_fn.Response(
            response=data,
            status=status,
            headers=headers or {},
            mimetype="application/json",
        )
        # Add a numeric status code for easier testing
        response.status_code = status
        return response

    return _create_response
