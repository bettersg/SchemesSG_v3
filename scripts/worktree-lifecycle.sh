#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  scripts/worktree-lifecycle.sh doctor [moved-worktree-path]
  scripts/worktree-lifecycle.sh remove <worktree-path>

`doctor` reports linked worktrees and stale administrative entries without
changing them. If a moved path is supplied, it prints the native repair command.
`remove` delegates to `git worktree remove`; Git refuses dirty or locked trees.
This script never forces removal, prunes metadata, or deletes branches.
EOF
}

command=${1:-}
case "$command" in
  --help|-h) usage; exit 0 ;;
  doctor)
    shift
    root=$(git rev-parse --show-toplevel)
    git -C "$root" worktree list --porcelain
    git -C "$root" worktree prune --dry-run --verbose
    if [ "$#" -eq 1 ]; then
      printf 'Moved worktree repair (review before running): git worktree repair %s\n' "$1"
    elif [ "$#" -gt 1 ]; then
      usage >&2
      exit 2
    fi
    ;;
  remove)
    shift
    [ "$#" -eq 1 ] || { usage >&2; exit 2; }
    root=$(git rev-parse --show-toplevel)
    target=$1
    current=$(cd "$root" && pwd -P)
    target_abs=$(cd "$(dirname "$target")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$target")")
    [ "$target_abs" != "$current" ] || {
      echo "Refusing to remove the current worktree; run from another checkout." >&2
      exit 1
    }
    git -C "$root" worktree remove "$target"
    printf 'Removed clean worktree: %s\n' "$target"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
