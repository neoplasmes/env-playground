#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
umask 077
mkdir -p .secrets .local
if [[ ! -f .secrets/local.env ]]; then
  cp infra/bootstrap/local.env.example .secrets/local.env
fi
if [[ ! -f .secrets/id_ed25519 ]]; then
  ssh-keygen -q -t ed25519 -N "" -C env-playground -f .secrets/id_ed25519
fi
printf 'Заполни .secrets/local.env: ключ Cloud.ru и твой IPv4 с /32. Секреты в Git не попадут.\n'
