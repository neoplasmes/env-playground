#!/usr/bin/env bash
set -euo pipefail

workflow_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
if [[ -x "$workflow_root/.cache/proto/bin/node" ]]; then
  source "$workflow_root/infra/bootstrap/activate.sh"
fi
pnpm --dir "$workflow_root/node/tools/agent-workflow" install --ignore-workspace --frozen-lockfile
