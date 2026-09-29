#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
terraform -chdir=infra/terraform fmt -check -recursive
export TF_CLI_CONFIG_FILE="$PWD/infra/terraform/terraform.rc"
terraform -chdir=infra/terraform init -backend=false -lockfile=readonly -input=false
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform/catalog init -backend=false -lockfile=readonly -input=false
terraform -chdir=infra/terraform/catalog validate
helm lint infra/charts/image-lab
helm template image-lab infra/charts/image-lab --namespace preview-1 >/dev/null
while IFS= read -r file; do bash -n "$file"; done < <(find infra -name '*.sh' -type f)
python -m compileall -q infra/bootstrap infra/ci infra/local
uv run --project python --frozen ruff check infra/bootstrap infra/ci infra/local
uv run --project python --frozen ruff format --check infra/bootstrap infra/ci infra/local
uv run --project python --package repo-style --frozen statement-padding infra/bootstrap infra/ci infra/local
