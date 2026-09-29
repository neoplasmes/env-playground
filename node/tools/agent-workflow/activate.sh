# Source from any directory to activate the existing project-local toolchain.
agent_toolchain_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
if [[ -x "$agent_toolchain_root/.cache/proto/bin/node" ]]; then
  source "$agent_toolchain_root/infra/bootstrap/activate.sh"
fi
# This checkout can use an existing Zig C-compiler shim instead of system cc.
if ! command -v cc >/dev/null && [[ -x "$agent_toolchain_root/.cache/native/cc" ]]; then
  export PATH="$agent_toolchain_root/.cache/native:$PATH"
  export ZIG_GLOBAL_CACHE_DIR="$agent_toolchain_root/.cache/zig"
fi
unset agent_toolchain_root
