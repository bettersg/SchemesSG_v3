#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT INT TERM
REMOTE="$TMP/remote.git"
SEED="$TMP/seed"
PRIMARY="$TMP/primary"
TASK="$TMP/task"

assert_fails() {
  if "$@" >"$TMP/out" 2>"$TMP/err"; then
    echo "Expected failure: $*" >&2
    exit 1
  fi
}

git init --bare "$REMOTE" >/dev/null
git init -b stg "$SEED" >/dev/null
git -C "$SEED" config user.email harness@example.test
git -C "$SEED" config user.name Harness
echo seed > "$SEED/seed.txt"
git -C "$SEED" add seed.txt
git -C "$SEED" commit -m seed >/dev/null
git -C "$SEED" remote add origin "$REMOTE"
git -C "$SEED" push -u origin stg >/dev/null
git --git-dir="$REMOTE" symbolic-ref HEAD refs/heads/stg
git clone "$REMOTE" "$PRIMARY" >/dev/null 2>&1

assert_fails sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-preflight.sh'"
(
  cd "$PRIMARY"
  "$ROOT/scripts/worktree-create.sh" feat/test "$TASK" >/dev/null
)
(
  cd "$TASK"
  "$ROOT/scripts/worktree-preflight.sh" >/dev/null
  assert_fails "$ROOT/scripts/worktree-preflight.sh" --hotfix
  git branch --unset-upstream
  assert_fails "$ROOT/scripts/worktree-preflight.sh"
  git branch --set-upstream-to=origin/feat/test >/dev/null
)
(
  cd "$TASK"
  echo dirty > dirty.txt
)
assert_fails sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-lifecycle.sh' remove '$TASK'"
rm "$TASK/dirty.txt"
sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-lifecycle.sh' doctor >/dev/null"
sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-lifecycle.sh' remove '$TASK' >/dev/null"
[ ! -e "$TASK" ] || { echo "Clean worktree was not removed" >&2; exit 1; }
assert_fails sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-create.sh' feat/test '$TMP/reused'"
assert_fails sh -c "cd '$PRIMARY' && '$ROOT/scripts/worktree-create.sh' stg '$TMP/protected'"
printf 'Worktree create/preflight tests passed.\n'
