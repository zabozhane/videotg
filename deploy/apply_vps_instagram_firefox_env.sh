#!/usr/bin/env bash
# На VPS: записать в .env YTDLP_COOKIES_FROM_BROWSER из профиля Firefox (ig-firefox) и перезапустить bot.
# Профиль ищется по cookies.sqlite (linuxserver/firefox: .config/mozilla/..., классика: .mozilla/...).
# Требует в корневом .env: VPS_HOST, VPS_USER, VPS_* для SSH, VPS_REMOTE_DIR (по умолчанию videotg).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет $ROOT/.env"
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

# shellcheck disable=SC2087
remote_script=$(cat <<EOF
set -euo pipefail
cd "\$HOME/${VPS_REMOTE_DIR}"
if [[ ! -f .env ]]; then echo "Нет .env в \$(pwd)"; exit 1; fi
if [[ ! -d data/firefox-ig ]]; then echo "Нет data/firefox-ig — сначала ig-firefox и логин в Instagram"; exit 1; fi
cookie=\$(find data/firefox-ig -name cookies.sqlite 2>/dev/null | head -1 || true)
if [[ -z "\${cookie:-}" ]]; then
  echo "Не найден cookies.sqlite под data/firefox-ig — откройте Firefox (ig-firefox), зайдите на instagram.com"
  exit 1
fi
prof=\$(dirname "\$cookie")
rel="\${prof#data/firefox-ig/}"
LINE="YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/\${rel}"
chmod a+r "\$cookie" 2>/dev/null || true
d="\$(dirname "\$cookie")"
chmod a+r "\$d/cookies.sqlite-wal" 2>/dev/null || true
chmod a+r "\$d/cookies.sqlite-shm" 2>/dev/null || true
cp .env ".env.bak.\$(date +%s)"
grep -v '^YTDLP_COOKIES_FROM_BROWSER=' .env > .env.tmp
mv .env.tmp .env
printf '\n# Instagram (Firefox на VPS, ig-firefox)\n%s\n' "\$LINE" >> .env
echo "==> Записано в .env: \$LINE"
docker compose up -d bot
docker compose ps bot
docker compose logs bot --tail 25
EOF
)

if [[ -n "$VPS_SSH_KEY_PATH" ]]; then
  ssh -i "$VPS_SSH_KEY_PATH" "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<<"$remote_script"
elif [[ -n "$VPS_SSH_PASSWORD" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "Нужен sshpass для VPS_SSH_PASSWORD"
    exit 1
  fi
  export SSHPASS="$VPS_SSH_PASSWORD"
  sshpass -e ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<<"$remote_script"
else
  ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<<"$remote_script"
fi
