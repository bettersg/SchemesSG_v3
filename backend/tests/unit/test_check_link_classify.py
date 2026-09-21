"""Unit tests for check_link.classify_link_result — the failure taxonomy the
weekly batch uses to decide inactivate-vs-quarantine."""
from utils.check_link import classify_link_result


def test_alive_results_classify_alive():
    assert classify_link_result({"alive": True, "status_code": 200}) == "alive"
    # alive-but-uncertain (403/429/Cloudflare/soft-404) is already alive=True
    assert classify_link_result({"alive": True, "status_code": 403}) == "alive"


def test_hard_dead_codes():
    for code in (400, 401, 404, 410):
        assert classify_link_result({"alive": False, "status_code": code}) == "hard_dead"


def test_server_errors_are_transient():
    for code in (500, 502, 503, 504):
        assert classify_link_result({"alive": False, "status_code": code}) == "transient"


def test_connection_failures_are_transient():
    # status_code 0 == timeout / DNS / conn-reset / SSL
    assert classify_link_result({"alive": False, "status_code": 0, "error": "DNS resolution failed"}) == "transient"
    assert classify_link_result({"alive": False, "status_code": 0, "error": "Connection timeout"}) == "transient"


def test_missing_status_code_defaults_transient_not_dead():
    # Never escalate to hard_dead on missing/unknown info.
    assert classify_link_result({"alive": False}) == "transient"
