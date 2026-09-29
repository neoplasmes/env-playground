#!/usr/bin/env bash
set -euo pipefail

workflow_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
tooling_dir="$workflow_root/node/tools/agent-workflow"
source "$tooling_dir/activate.sh"
cd "$workflow_root"

case "${1:-}" in
  terraform-mcp)
    shift
    exec "$workflow_root/.cache/agent-workflow/bin/terraform-mcp-server" stdio --toolsets=registry "$@"
    ;;
  commitlint)
    shift
    exec "$tooling_dir/node_modules/.bin/commitlint" --config "$tooling_dir/commitlint.config.cjs" "$@"
    ;;
  playwright-cli)
    shift
    export PLAYWRIGHT_BROWSERS_PATH="$workflow_root/.cache/playwright"
    exec node "$tooling_dir/browser-cli.mjs" "$@"
    ;;
  next-devtools-mcp|playwright)
    tool=$1
    shift
    export PLAYWRIGHT_BROWSERS_PATH="$workflow_root/.cache/playwright"
    exec "$tooling_dir/node_modules/.bin/$tool" "$@"
    ;;
  *)
    printf 'Usage: %s {commitlint|playwright-cli|next-devtools-mcp|terraform-mcp|playwright} [args...]\n' "$0" >&2
    exit 2
    ;;
esac
