#!/usr/bin/env bash
# На VPS: записать в .env YTDLP_COOKIES_FROM_BROWSER из профиля Firefox (ig-firefox) и перезапустить bot.
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

if [[ -n "$VPS_SSH_KEY_PATH" ]]; then
  ssh -i "$VPS_SSH_KEY_PATH" "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<EOF
set -euo pipefail
cd "\$HOME/${VPS_REMOTE_DIR}"
if [[ ! -f .env ]]; then echo "Нет .env в \$(pwd)"; exit 1; fi
BASE="data/firefox-ig/.mozilla/firefox"
if [[ ! -d "\$BASE" ]]; then echo "Нет каталога \$BASE — сначала залогиньтесь в ig-firefox"; exit 1; fi
PROFILE=\$(ls -1 "\$BASE" | grep -E '\.(default|default-release)' | head -1 || true)
if [[ -z "\${PROFILE:-}" ]]; then echo "Не найден default-профиль в \$BASE:"; ls -la "\$BASE"; exit 1; fi
LINE="YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/.mozilla/firefox/\${PROFILE}"
cp .env ".env.bak.\$(date +%s)"
grep -v '^YTDLP_COOKIES_FROM_BROWSER=' .env > .env.tmp
mv .env.tmp .env
printf '\n# Instagram (Firefox на VPS, ig-firefox)\n%s\n' "\$LINE" >> .env
echo "==> Записано в .env: \$LINE"
docker compose up -d bot
docker compose ps bot
EOF
elif [[ -n "$VPS_SSH_PASSWORD" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "Нужен sshpass для VPS_SSH_PASSWORD"
    exit 1
  fi
  export SSHPASS="$VPS_SSH_PASSWORD"
  sshpass -e ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<EOF
set -euo pipefail
cd "\$HOME/${VPS_REMOTE_DIR}"
if [[ ! -f .env ]]; then echo "Нет .env в \$(pwd)"; exit 1; fi
BASE="data/firefox-ig/.mozilla/firefox"
if [[ ! -d "\$BASE" ]]; then echo "Нет каталога \$BASE — сначала залогиньтесь в ig-firefox"; exit 1; fi
PROFILE=\$(ls -1 "\$BASE" | grep -E '\.(default|default-release)' | head -1 || true)
if [[ -z "\${PROFILE:-}" ]]; then echo "Не найден default-профиль в \$BASE:"; ls -la "\$BASE"; exit 1; fi
LINE="YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/.mozilla/firefox/\${PROFILE}"
cp .env ".env.bak.\$(date +%s)"
grep -v '^YTDLP_COOKIES_FROM_BROWSER=' .env > .env.tmp
mv .env.tmp .env
printf '\n# Instagram (Firefox на VPS, ig-firefox)\n%s\n' "\$LINE" >> .env
echo "==> Записано в .env: \$LINE"
docker compose up -d bot
docker compose ps bot
EOF
else
  ssh "${SSH_EXTRA[@]}" "${VPS_USER}@${VPS_HOST}" bash -s <<EOF
set -euo pipefail
cd "\$HOME/${VPS_REMOTE_DIR}"
if [[ ! -f .env ]]; then echo "Нет .env в \$(pwd)"; exit 1; fi
BASE="data/firefox-ig/.mozilla/firefox"
if [[ ! -d "\$BASE" ]]; then echo "Нет каталога \$BASE — сначала залогиньтесь в ig-firefox"; exit 1; fi
PROFILE=\$(ls -1 "\$BASE" | grep -E '\.(default|default-release)' | head -1 || true)
if [[ -z "\${PROFILE:-}" ]]; then echo "Не найден default-профиль в \$BASE:"; ls -la "\$BASE"; exit 1; fi
LINE="YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/.mozilla/firefox/\${PROFILE}"
cp .env ".env.bak.\$(date +%s)"
grep -v '^YTDLP_COOKIES_FROM_BROWSER=' .env > .env.tmp
mv .env.tmp .env
printf '\n# Instagram (Firefox на VPS, ig-firefox)\n%s\n' "\$LINE" >> .env
echo "==> Записано в .env: \$LINE"
docker compose up -d bot
docker compose ps bot
EOF
fi
