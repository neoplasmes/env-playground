#!/usr/bin/env bash
set -euo pipefail

workflow_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
source "$workflow_root/node/tools/agent-workflow/activate.sh"
pnpm --dir "$workflow_root/node/tools/agent-workflow" install --ignore-workspace --frozen-lockfile
