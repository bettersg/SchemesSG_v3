#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

assert_symlink() {
  path=$1
  expected=$2
  if [ ! -L "$path" ]; then
    printf 'FAIL: %s must be a symlink\n' "$path" >&2
    exit 1
  fi
  actual=$(readlink "$path")
  if [ "$actual" != "$expected" ]; then
    printf 'FAIL: %s points to %s, expected %s\n' "$path" "$actual" "$expected" >&2
    exit 1
  fi
}

assert_line() {
  path=$1
  expected=$2
  description=$3
  if ! grep -Fqx -- "$expected" "$path"; then
    printf 'FAIL: %s is missing from %s\n' "$description" "$path" >&2
    exit 1
  fi
}

for instructions in "$ROOT/AGENTS.md" "$ROOT/backend/AGENTS.md" "$ROOT/frontend/AGENTS.md"; do
  if [ ! -s "$instructions" ]; then
    printf 'FAIL: missing instruction source %s\n' "$instructions" >&2
    exit 1
  fi
  lines=$(wc -l < "$instructions" | tr -d ' ')
  if [ "$lines" -gt 200 ]; then
    printf 'FAIL: %s has %s lines; limit is 200\n' "$instructions" "$lines" >&2
    exit 1
  fi
done

assert_line "$ROOT/docs/verification.md" "## Test impact" "test-impact policy heading"
T="$ROOT/pull_request_template.md"
assert_line "$T" "## TLDR" "TLDR PR heading"
assert_line "$T" "## User Flow" "user-flow PR heading"
assert_line "$T" "## Relevant issues" "relevant-issues PR heading"
assert_line "$T" "## Task isolation" "task-isolation PR heading"
assert_line "$T" "## Test impact" "test-impact PR heading"
assert_line "$T" "- Observable behavior changes:" "observable-behavior field"
assert_line "$T" "- Focused regression tests:" "focused-regression-test field"
assert_line "$T" "- Red-before evidence (bug fixes, when practical):" "red-before field"
assert_line "$T" "- Green-after evidence:" "green-after field"
assert_line "$T" "- No-test reason (if applicable):" "no-test-reason field"
assert_line "$T" "- Substitute evidence (if applicable):" "substitute-evidence field"
assert_line "$T" "## Verification evidence" "verification-evidence PR heading"
assert_line "$T" "## Pre-Submission checklist" "pre-submission checklist heading"
assert_line "$T" "## Screenshots / Proof of Fix" "proof-of-fix heading"
assert_line "$T" "### Before (<hash>)" "proof-of-fix before heading"
assert_line "$T" "### After (<hash>)" "proof-of-fix after heading"
assert_line "$T" "## Caveats (if any)" "caveats heading"
assert_line "$T" "## Final Attestation" "final-attestation heading"

assert_symlink "$ROOT/CLAUDE.md" AGENTS.md
assert_symlink "$ROOT/backend/CLAUDE.md" AGENTS.md
assert_symlink "$ROOT/frontend/CLAUDE.md" AGENTS.md

"$ROOT/scripts/test-worktree.sh"
printf 'Harness integrity checks passed.\n'
