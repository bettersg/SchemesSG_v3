"""Regression tests for secretless backend module imports."""

import importlib
import sys

import pytest
from fb_manager.firebaseManager import FirebaseManager


@pytest.mark.parametrize(
    "module_name",
    [
        "feedback.feedback",
        "update_scheme.update_scheme",
        "slack_integration.storage",
        "main",
        "scripts.run_link_check_and_reindex",
    ],
)
def test_import_does_not_initialize_firebase_or_contact_network(module_name, mocker):
    """Importing a backend module must not initialize Firebase or use a network."""
    sys.modules.pop(module_name, None)
    import_in_progress = True

    def reject_network(event, _args):
        if import_in_progress and event in {"socket.connect", "socket.getaddrinfo"}:
            raise AssertionError(f"Network contacted during import: {event}")

    sys.addaudithook(reject_network)
    constructor = mocker.patch.object(
        FirebaseManager,
        "__new__",
        side_effect=AssertionError("Firebase initialized during import"),
    )

    try:
        importlib.import_module(module_name)
    finally:
        import_in_progress = False
        sys.modules.pop(module_name, None)

    constructor.assert_not_called()
