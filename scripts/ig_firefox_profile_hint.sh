#!/usr/bin/env sh
# Подсказка для YTDLP_COOKIES_FROM_BROWSER после логина в сервисе ig-firefox.
# Запуск на VPS из каталога проекта: sh scripts/ig_firefox_profile_hint.sh

set -e
BASE="${1:-./data/firefox-ig/.mozilla/firefox}"

if [ ! -d "$BASE" ]; then
  echo "Каталога ещё нет: $BASE"
  echo "Запустите Firefox на сервере: docker compose --profile ig-login up -d"
  echo "Откройте UI (см. README), дождитесь первого запуска браузера, затем снова этот скрипт."
  exit 1
fi

echo "Папки профилей:"
ls -1 "$BASE" 2>/dev/null || true
echo ""
guess="$(ls -1 "$BASE" 2>/dev/null | grep -E '\.(default|default-release)' | head -1 || true)"
if [ -n "$guess" ]; then
  echo "Добавьте в .env на VPS (в контейнере бота путь к профилю — /igfirefox/...):"
  echo "YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/.mozilla/firefox/${guess}"
else
  echo "Подставьте имя одной из папок выше:"
  echo "YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/.mozilla/firefox/<имя_папки>"
fi
