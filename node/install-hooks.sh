#!/usr/bin/env bash
set -euo pipefail

playground_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$playground_root"
existing=$(git config --get core.hooksPath || true)
if [[ -n "$existing" && "$existing" != ".githooks" ]]; then
  printf 'Existing hooksPath is %s; integrate the commit-msg hook without replacing it.\n' "$existing" >&2
  exit 1
fi
git config --local core.hooksPath .githooks
printf 'Enabled the project commit-msg hook.\n'
