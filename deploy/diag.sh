#!/usr/bin/env bash
# Состояние бота на VPS: docker compose ps + последние логи (без rsync).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет $ROOT/.env — скопируйте из .env.example."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

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

SSH_EXTRA=(-p "$VPS_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25)
RDIR="$VPS_REMOTE_DIR"
REMOTE_CMD="cd \$HOME/${RDIR} && docker compose ps -a && echo ========== bot logs ========== && docker compose logs bot --tail 200"

if [[ -n "$VPS_SSH_KEY_PATH" ]]; then
  if [[ ! -f "$VPS_SSH_KEY_PATH" ]]; then
    echo "Ключ не найден: $VPS_SSH_KEY_PATH"
    exit 1
  fi
  ssh -i "$VPS_SSH_KEY_PATH" "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" "$REMOTE_CMD"
elif [[ -n "$VPS_SSH_PASSWORD" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "Нужен sshpass для пароля (brew install hudochenkov/sshpass/sshpass)"
    exit 1
  fi
  export SSHPASS="$VPS_SSH_PASSWORD"
  sshpass -e ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" "$REMOTE_CMD"
else
  ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" "$REMOTE_CMD"
fi
