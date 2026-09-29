#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
mkdir -p .local
export TF_CLI_CONFIG_FILE="$PWD/infra/terraform/terraform.rc"
if [[ -f .secrets/local.env ]]; then
  set -a
  source .secrets/local.env
  set +a
fi
action="${1:-plan}"
case "$action" in
  catalog)
    terraform -chdir=infra/terraform/catalog init
    terraform -chdir=infra/terraform/catalog apply -auto-approve
    ;;
  init) terraform -chdir=infra/terraform init ;;
  check) terraform -chdir=infra/terraform fmt -check; terraform -chdir=infra/terraform validate ;;
  plan)
    : "${TF_VAR_auth_key_id:?Заполни .secrets/local.env}"
    : "${TF_VAR_auth_secret:?Заполни .secrets/local.env}"
    : "${TF_VAR_admin_cidr:?Укажи свой IPv4/32}"
    terraform -chdir=infra/terraform plan -out=../../.local/create.tfplan
    ;;
  apply) terraform -chdir=infra/terraform apply ../../.local/create.tfplan ;;
  destroy-plan) terraform -chdir=infra/terraform plan -destroy -out=../../.local/destroy.tfplan ;;
  destroy) terraform -chdir=infra/terraform apply ../../.local/destroy.tfplan ;;
  output) terraform -chdir=infra/terraform output -json ;;
  *) printf 'Unknown action: %s\n' "$action" >&2; exit 2 ;;
esac
