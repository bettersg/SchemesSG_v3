#!/bin/sh
set -eu

usage() {
  cat <<'EOF'
Usage: scripts/worktree-preflight.sh [--hotfix]

Validates that the current checkout is a linked task worktree with a safe
branch, matching remote upstream, and recorded selected-base ancestry.
EOF
}

hotfix=false
case "${1:-}" in
  --help|-h) usage; exit 0 ;;
  --hotfix) hotfix=true; shift ;;
  '') ;;
  *) usage >&2; exit 2 ;;
esac
[ "$#" -eq 0 ] || { usage >&2; exit 2; }

root=$(git rev-parse --show-toplevel)
git_dir=$(git rev-parse --git-dir)
common_dir=$(git rev-parse --git-common-dir)
[ "$(cd "$git_dir" && pwd -P)" != "$(cd "$common_dir" && pwd -P)" ] || {
  echo "Refusing the shared checkout; create a task worktree first." >&2
  exit 1
}

branch=$(git branch --show-current)
case "$branch" in ''|stg|main) echo "Refusing protected or detached branch: ${branch:-detached}" >&2; exit 1 ;; esac
upstream=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
[ "$upstream" = "origin/$branch" ] || { echo "Expected upstream origin/$branch, found ${upstream:-none}" >&2; exit 1; }

expected_ref=stg
$hotfix && expected_ref=main
base_file="$git_dir/harness-base"
ref_file="$git_dir/harness-base-ref"
[ -s "$base_file" ] && [ -s "$ref_file" ] || { echo "Missing recorded worktree base; use worktree-create.sh." >&2; exit 1; }
base_sha=$(cat "$base_file")
base_ref=$(cat "$ref_file")
[ "$base_ref" = "$expected_ref" ] || { echo "Expected base $expected_ref, recorded $base_ref" >&2; exit 1; }
git merge-base --is-ancestor "$base_sha" HEAD || { echo "Recorded base is not an ancestor of HEAD" >&2; exit 1; }

printf 'Preflight passed: %s -> %s, base origin/%s (%s)\n' "$branch" "$upstream" "$base_ref" "$base_sha"
