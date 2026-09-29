#!/usr/bin/env bash
set -euo pipefail

node_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
workflow_root=$(cd "$node_root/.." && pwd)
source "$node_root/activate.sh"
cd "$workflow_root"

case "${1:-}" in
  commitlint)
    shift
    exec "$node_root/node_modules/.bin/commitlint" --config "$node_root/commitlint.config.cjs" "$@"
    ;;
  playwright)
    shift
    export PLAYWRIGHT_BROWSERS_PATH="$workflow_root/.cache/playwright"
    exec "$node_root/node_modules/.bin/playwright" "$@"
    ;;
  *)
    printf 'Usage: %s {commitlint|playwright} [args...]\n' "$0" >&2
    exit 2
    ;;
esac
