"""Public CLI contract for the approved backend coverage ratchet."""

import json
import subprocess
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).parents[2]
CHECKER = BACKEND_ROOT / "scripts" / "check_coverage.py"


def run_checker(*, covered_lines: int, statements: int, covered_branches: int, branches: int):
    payload = {
        "totals": {
            "covered_lines": covered_lines,
            "num_statements": statements,
            "covered_branches": covered_branches,
            "num_branches": branches,
        }
    }
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_coverage_ratchet_accepts_approved_floors():
    result = run_checker(
        covered_lines=2170,
        statements=4133,
        covered_branches=383,
        branches=1152,
    )

    assert result.returncode == 0
    assert "statements 52.50%" in result.stdout
    assert "branches 33.25%" in result.stdout


def test_coverage_ratchet_rejects_statement_regression():
    result = run_checker(
        covered_lines=2169,
        statements=4133,
        covered_branches=383,
        branches=1152,
    )

    assert result.returncode == 1
    assert "statement coverage regressed: 52.48% < 52.50%" in result.stderr


def test_coverage_ratchet_rejects_branch_regression():
    result = run_checker(
        covered_lines=2170,
        statements=4133,
        covered_branches=382,
        branches=1152,
    )

    assert result.returncode == 1
    assert "branch coverage regressed: 33.16% < 33.24%" in result.stderr


def test_coverage_ratchet_reports_each_regressed_metric():
    result = run_checker(
        covered_lines=2169,
        statements=4133,
        covered_branches=382,
        branches=1152,
    )

    assert result.returncode == 1
    assert "statement coverage regressed" in result.stderr
    assert "branch coverage regressed" in result.stderr
