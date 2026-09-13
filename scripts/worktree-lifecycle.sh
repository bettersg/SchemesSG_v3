#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage:
  scripts/worktree-lifecycle.sh doctor [moved-worktree-path]
  scripts/worktree-lifecycle.sh remove <worktree-path>

`doctor` reports linked worktrees and stale administrative entries without
changing them, and names every task worktree whose pull request has already
merged or closed, so finished trees do not accumulate. If a moved path is
supplied, it prints the native repair command.
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
    # Which trees are finished. Silent without gh, or without a GitHub remote to
    # ask: a missing pull request is not a reason to fail a diagnostic.
    if command -v gh >/dev/null 2>&1; then
      git -C "$root" worktree list --porcelain |
        awk '/^worktree /{path=$2} /^branch /{sub(/^refs\/heads\//, "", $2); print path "\t" $2}' |
        while IFS="$(printf '\t')" read -r wt branch; do
          case "$branch" in stg | main) continue ;; esac
          state=$(gh pr list --head "$branch" --state all --limit 1 \
            --json state,number --jq '.[0] | "\(.state) #\(.number)"' 2>/dev/null) || continue
          case "$state" in
            MERGED* | CLOSED*)
              printf 'Finished: %s is %s — remove it: scripts/worktree-lifecycle.sh remove %s\n' \
                "$branch" "$state" "$wt"
              ;;
            OPEN*) printf 'In review: %s is %s — keep %s\n' "$branch" "$state" "$wt" ;;
          esac
        done
    fi
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
