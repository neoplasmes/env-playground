# Source from any directory to activate the existing project-local toolchain.
node_toolchain_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ -x "$node_toolchain_root/.cache/proto/bin/node" ]]; then
  source "$node_toolchain_root/infra/bootstrap/activate.sh"
fi
# This checkout can use an existing Zig C-compiler shim instead of system cc.
if ! command -v cc >/dev/null && [[ -x "$node_toolchain_root/.cache/native/cc" ]]; then
  export PATH="$node_toolchain_root/.cache/native:$PATH"
  export ZIG_GLOBAL_CACHE_DIR="$node_toolchain_root/.cache/zig"
fi
unset node_toolchain_root
