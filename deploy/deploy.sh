#!/usr/bin/env bash
# Деплой на VPS: rsync проекта + docker compose на сервере.
# Переменные в .env в корне репозитория (см. .env.example). Пароль в .env — риск; предпочтительнее VPS_SSH_KEY_PATH.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет файла $ROOT/.env — скопируйте из .env.example и заполните VPS_* и секреты бота."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

# Поддержка нижнего регистра из .env
VPS_HOST="${VPS_HOST:-${vps_host:-}}"
VPS_USER="${VPS_USER:-${vps_user:-}}"
VPS_PORT="${VPS_PORT:-${vps_port:-22}}"
VPS_SSH_KEY_PATH="${VPS_SSH_KEY_PATH:-${vps_ssh_key_path:-}}"
VPS_SSH_PASSWORD="${VPS_SSH_PASSWORD:-${vps_ssh_password:-}}"
VPS_REMOTE_DIR="${VPS_REMOTE_DIR:-${vps_remote_dir:-videotg}}"

if [[ -z "$VPS_HOST" || -z "$VPS_USER" ]]; then
  echo "Задайте VPS_HOST и VPS_USER в .env"
  exit 1
fi

SSH_EXTRA=(-p "$VPS_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20)
RSYNC_SSH=(ssh "${SSH_EXTRA[@]}")

if [[ -n "$VPS_SSH_KEY_PATH" ]]; then
  if [[ ! -f "$VPS_SSH_KEY_PATH" ]]; then
    echo "Файл ключа не найден: $VPS_SSH_KEY_PATH"
    exit 1
  fi
  RSYNC_SSH=(ssh -i "$VPS_SSH_KEY_PATH" "${SSH_EXTRA[@]}")
elif [[ -n "$VPS_SSH_PASSWORD" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "Для пароля нужен sshpass (brew install hudochenkov/sshpass/sshpass или apt install sshpass)"
    exit 1
  fi
  RSYNC_SSH=(sshpass -e ssh "${SSH_EXTRA[@]}")
  export SSHPASS="$VPS_SSH_PASSWORD"
fi

REMOTE="${VPS_USER}@${VPS_HOST}:~/${VPS_REMOTE_DIR}/"
RSYNC_E="${RSYNC_SSH[*]}"

echo "==> Rsync в $REMOTE (без .venv и кэшей)"
rsync -az --delete \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude '*.pyc' \
  -e "$RSYNC_E" \
  "$ROOT/" \
  "$REMOTE"

echo "==> Docker Compose на сервере"
if [[ -n "$VPS_SSH_KEY_PATH" ]]; then
  ssh -i "$VPS_SSH_KEY_PATH" "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" \
    "set -euo pipefail; cd \"\$HOME/${VPS_REMOTE_DIR}\" && (docker compose up --build -d || docker-compose up --build -d)"
elif [[ -n "$VPS_SSH_PASSWORD" ]]; then
  sshpass -e ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" \
    "set -euo pipefail; cd \"\$HOME/${VPS_REMOTE_DIR}\" && (docker compose up --build -d || docker-compose up --build -d)"
else
  ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" \
    "set -euo pipefail; cd \"\$HOME/${VPS_REMOTE_DIR}\" && (docker compose up --build -d || docker-compose up --build -d)"
fi

echo "==> Готово. Логи: ssh … 'cd ~/${VPS_REMOTE_DIR} && docker compose logs -f --tail=80 bot'"
