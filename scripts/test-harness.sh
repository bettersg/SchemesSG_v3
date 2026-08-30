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

assert_symlink "$ROOT/CLAUDE.md" AGENTS.md
assert_symlink "$ROOT/backend/CLAUDE.md" AGENTS.md
assert_symlink "$ROOT/frontend/CLAUDE.md" AGENTS.md

"$ROOT/scripts/test-worktree.sh"
printf 'Harness integrity checks passed.\n'
