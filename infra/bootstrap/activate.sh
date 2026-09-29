# Source this file to use the project-local toolchain, if installed in .cache/proto.
playground_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export PROTO_HOME="$playground_root/.cache/proto"
export CARGO_HOME="$playground_root/.cache/cargo"
export RUSTUP_HOME="$playground_root/.cache/rustup"
export UV_CACHE_DIR="$playground_root/.cache/uv"
export PROTO_NODE_VERSION=26.10.0
export PATH="$PROTO_HOME/bin:$PROTO_HOME/shims:$CARGO_HOME/bin:$PATH"
unset playground_root
