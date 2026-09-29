#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
: "${DEPLOY_KUBECONFIG:?Missing deployment credential}"
: "${REGISTRY_TOKEN:?Missing GHCR credential}"
delivery_tmp=$(mktemp -d)
trap 'rm -rf "$delivery_tmp"' EXIT
export KUBECONFIG="$delivery_tmp/kubeconfig"
export DOCKER_CONFIG="$delivery_tmp/docker"
export BUILDKIT_TLS_DIR="$delivery_tmp/tls"
mkdir -p "$DOCKER_CONFIG" "$BUILDKIT_TLS_DIR"
python - <<'PY'
import base64, json, os
from pathlib import Path
Path(os.environ['KUBECONFIG']).write_text(os.environ['DEPLOY_KUBECONFIG'])
for suffix, variable in [('ca.pem','BUILDKIT_CA'), ('cert.pem','BUILDKIT_CERT'), ('key.pem','BUILDKIT_KEY')]:
    (Path(os.environ['BUILDKIT_TLS_DIR']) / suffix).write_text(os.environ[variable])
auth = base64.b64encode(f"{os.environ['REGISTRY_USER']}:{os.environ['REGISTRY_TOKEN']}".encode()).decode()
(Path(os.environ['DOCKER_CONFIG']) / 'config.json').write_text(json.dumps({'auths': {'ghcr.io': {'auth': auth}}}))
PY
python infra/ci/reconcile.py
