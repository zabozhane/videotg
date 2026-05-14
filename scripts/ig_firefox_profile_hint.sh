#!/usr/bin/env sh
# Подсказка для YTDLP_COOKIES_FROM_BROWSER после логина в сервисе ig-firefox.
# Запуск на VPS из каталога проекта: sh scripts/ig_firefox_profile_hint.sh

set -e
ROOT="${1:-./data/firefox-ig}"

if [ ! -d "$ROOT" ]; then
  echo "Нет каталога: $ROOT"
  echo "Запустите: docker compose --profile ig-login up -d"
  exit 1
fi

cookie="$(find "$ROOT" -name cookies.sqlite 2>/dev/null | head -1 || true)"
if [ -z "$cookie" ]; then
  echo "Не найден cookies.sqlite в $ROOT — откройте ig-firefox, зайдите на instagram.com"
  exit 1
fi

prof="$(dirname "$cookie")"
rel="${prof#${ROOT}/}"
echo "Профиль (на хосте): $prof"
echo ""
echo "Добавьте в .env на VPS (в контейнере бота том смонтирован как /igfirefox):"
echo "YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/${rel}"
