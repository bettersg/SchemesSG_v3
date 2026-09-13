#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage: scripts/worktree-create.sh [--hotfix] <branch> [path]

Fetches the selected remote base (origin/stg by default; origin/main with
--hotfix), creates a sibling task worktree, pushes the empty branch, verifies
its upstream, and records the base SHA for preflight.
EOF
}

hotfix=false
case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --hotfix) hotfix=true; shift ;;
esac

branch=${1:-}
[ -n "$branch" ] || { usage >&2; exit 2; }
case "$branch" in stg|main) echo "Refusing protected branch: $branch" >&2; exit 1 ;; esac

root=$(git rev-parse --show-toplevel)
base=stg
$hotfix && base=main
git -C "$root" fetch origin "$base"
base_sha=$(git -C "$root" rev-parse "origin/$base")
path=${2:-"$(dirname "$root")/$(basename "$root")-${branch##*/}"}

if git -C "$root" show-ref --verify --quiet "refs/heads/$branch" || git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
  echo "Branch already exists: $branch" >&2
  exit 1
fi

# --no-track prevents the task branch from inheriting origin/<base> as upstream.
git -C "$root" worktree add --no-track -b "$branch" "$path" "$base_sha"
git -C "$path" push -u origin "$branch"
upstream=$(git -C "$path" rev-parse --abbrev-ref '@{upstream}')
[ "$upstream" = "origin/$branch" ] || { echo "Unexpected upstream: $upstream" >&2; exit 1; }
printf '%s\n' "$base_sha" > "$(git -C "$path" rev-parse --git-dir)/harness-base"
printf '%s\n' "$base" > "$(git -C "$path" rev-parse --git-dir)/harness-base-ref"
printf 'Created %s at %s from origin/%s (%s)\n' "$branch" "$path" "$base" "$base_sha"
