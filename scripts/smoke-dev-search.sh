#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PRIMARY=$(git -C "$ROOT" worktree list --porcelain | sed -n '1s/^worktree //p')
export SCHEMESSG_DEV_CONFIG_DIR=${SCHEMESSG_DEV_CONFIG_DIR:-"$PRIMARY/backend/functions"}
export SCHEMESSG_FRONTEND_ENV=${SCHEMESSG_FRONTEND_ENV:-"$PRIMARY/frontend/.env.staging"}
slug=$(git -C "$ROOT" branch --show-current | tr '/_' '--' | tr -cd '[:alnum:]-')
export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-"schemessg-dev-${slug:-smoke}"}
export DEV_SMOKE_FRONTEND_PORT=${DEV_SMOKE_FRONTEND_PORT:-3000}
export DEV_SMOKE_BACKEND_PORT=${DEV_SMOKE_BACKEND_PORT:-15001}
COMPOSE="docker compose -f $ROOT/compose.dev-smoke.yml"
logs="$ROOT/.smoke-logs"
mkdir -p "$logs"

for required in "$SCHEMESSG_DEV_CONFIG_DIR/.env" "$SCHEMESSG_DEV_CONFIG_DIR/creds.json" "$SCHEMESSG_FRONTEND_ENV"; do
  [ -s "$required" ] || { printf 'Missing dev smoke prerequisite: %s\n' "$required" >&2; exit 1; }
done

grep -q '^FB_PROJECT_ID=schemessg-v3-dev$' "$SCHEMESSG_DEV_CONFIG_DIR/.env" || {
  echo "Backend config is not for schemessg-v3-dev; refusing smoke." >&2
  exit 1
}
grep -q '^NEXT_PUBLIC_FIREBASE_PROJECT_ID=schemessg-v3-dev$' "$SCHEMESSG_FRONTEND_ENV" || {
  echo "Frontend config is not for schemessg-v3-dev; refusing smoke." >&2
  exit 1
}

cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    $COMPOSE logs --no-color > "$logs/dev-search-compose.log" 2>&1 || true
    printf 'Dev search smoke failed; diagnostics: %s/dev-search-compose.log\n' "$logs" >&2
  fi
  $COMPOSE down --remove-orphans >/dev/null 2>&1 || true
  exit "$status"
}
trap cleanup EXIT INT TERM

$COMPOSE up --build --wait --wait-timeout 240
(
  cd "$ROOT/frontend"
  DEV_SMOKE_BASE_URL="http://localhost:$DEV_SMOKE_FRONTEND_PORT" \
    npx playwright test --config=playwright.dev-smoke.config.ts
)
printf 'Dev search smoke passed against schemessg-v3-dev.\n'
