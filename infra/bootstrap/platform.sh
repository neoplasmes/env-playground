#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
set -a
source .secrets/local.env
set +a
export KUBECONFIG="$PWD/.secrets/kubeconfig"
: "${ACME_EMAIL:?Укажи email для сертификатов}"
: "${WOODPECKER_GITHUB_CLIENT:?Создай GitHub OAuth App}"
: "${WOODPECKER_GITHUB_SECRET:?Укажи OAuth secret в .secrets/local.env}"
: "${REGISTRY_TOKEN:?Укажи GHCR token в .secrets/local.env}"
helm upgrade --install cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.21.2 --namespace cert-manager --create-namespace \
  --set crds.enabled=true --wait --timeout 5m
python infra/bootstrap/platform_config.py
python infra/bootstrap/delivery.py
