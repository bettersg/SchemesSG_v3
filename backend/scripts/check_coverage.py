"""Enforce the parent-approved backend coverage ratchet."""

import json
import sys


STATEMENT_FLOOR = 52.50
BRANCH_FLOOR = 33.24


def percentage(covered: int, total: int) -> float:
    return covered / total * 100


def main() -> int:
    totals = json.load(sys.stdin)["totals"]
    statements = percentage(totals["covered_lines"], totals["num_statements"])
    branches = percentage(totals["covered_branches"], totals["num_branches"])

    regressions = []
    if statements < STATEMENT_FLOOR:
        regressions.append(f"Backend statement coverage regressed: {statements:.2f}% < {STATEMENT_FLOOR:.2f}%")
    if branches < BRANCH_FLOOR:
        regressions.append(f"Backend branch coverage regressed: {branches:.2f}% < {BRANCH_FLOOR:.2f}%")

    if regressions:
        print(*regressions, sep="\n", file=sys.stderr)
        return 1

    print(
        "Backend coverage ratchet passed: "
        f"statements {statements:.2f}% >= {STATEMENT_FLOOR:.2f}%; "
        f"branches {branches:.2f}% >= {BRANCH_FLOOR:.2f}%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
