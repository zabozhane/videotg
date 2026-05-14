# Async Telegram Video Publisher Bot

## Project idea
Telegram-бот на Python: по ссылке асинхронно качает видео с Instagram, YouTube и Reddit (через yt-dlp), проверяет размер, публикует в заданный канал и удаляет временные файлы.

## Требования
- Python 3.12+
- [ffmpeg](https://ffmpeg.org/) (для склейки потоков yt-dlp)
- Токен бота и права на публикацию в канале

## Быстрый старт (локально)
```bash
cd /path/to/insta_download
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Заполните BOT_TOKEN и TELEGRAM_CHANNEL_ID
python -m videobot
```

Переменные окружения (или `.env`): см. `.env.example`. Обязательны `BOT_TOKEN` и `TELEGRAM_CHANNEL_ID` (например `@mychannel` или `-100…`).

## Локально: Instagram через Chrome (проще всего)

1. В **Google Chrome** на этом Mac зайдите на [instagram.com](https://www.instagram.com) и **войдите в аккаунт** (тот же, с которого виден Reel).
2. В **`.env`** должно быть `YTDLP_COOKIES_FROM_BROWSER=chrome` (уже есть в `.env.example`). yt-dlp сам прочитает cookies из профиля Chrome — **отдельный файл cookies.txt не нужен**.
3. Перезапустите бота и отправьте ссылку на Reel.

Если Chrome спросит доступ к связке ключей (Keychain) при первом скачивании — разрешите. На **VPS без Chrome** этот способ не подойдёт — там используйте `YTDLP_COOKIEFILE` (файл Netscape), см. ниже.

## Локально: файл cookies (если не хотите отдавать доступ к Chrome)

**Какой браузер лучше:** оптимально **Google Chrome** или другой **Chromium** (Brave, Microsoft Edge). Для них есть расширение **Get cookies.txt LOCALLY** в [Chrome Web Store](https://chromewebstore.google.com/search/Get%20cookies.txt%20LOCALLY) — экспорт идёт **только на диск**, без отправки cookies на чужие серверы (избегайте одноимённых расширений без «LOCALLY»). **Firefox** подойдёт, если найдёте расширение с экспортом в формат **Netscape `cookies.txt`** (такой же формат ожидает yt-dlp).

**Шаги:** установите расширение → войдите в Instagram → экспорт cookies для **instagram.com** → сохраните как `secrets/instagram_cookies.txt` → `chmod 600 secrets/instagram_cookies.txt` → в `.env` укажите `YTDLP_COOKIEFILE=/полный/путь/...` и **уберите** `YTDLP_COOKIES_FROM_BROWSER`, если не хотите читать cookies из браузера.

Если Instagram разлогинил или сменили пароль — повторите экспорт или снова войдите в Chrome.

## Docker
```bash
cp .env.example .env
# заполните BOT_TOKEN, TELEGRAM_CHANNEL_ID; на VPS — YTDLP_COOKIEFILE (см. ниже)
docker compose up --build -d
```

- **Healthcheck снаружи:** порт хоста задаётся `PUBLIC_HEALTH_PORT` (по умолчанию 8080), внутри контейнера сервис слушает **8080** (`HEALTH_PORT` переопределяется в `docker-compose.yml`). Проверка: `curl -s http://127.0.0.1:${PUBLIC_HEALTH_PORT:-8080}/health`.
- **Логи и temp:** `./logs` на хосте и том `bot_temp` для временных файлов.
- **Instagram в контейнере:** задайте `YTDLP_COOKIEFILE=/run/instagram_cookies.txt` и volume к `data/instagram_cookies.txt`, либо войдите через опциональный Firefox (`ig-login`, см. раздел **Instagram и VPS**).

## Деплой на VPS (кратко)

1. **Сервер:** Ubuntu 22.04+ (или аналог), установлены [Docker Engine](https://docs.docker.com/engine/install/) и Docker Compose plugin.
2. Скопируйте проект: `git clone …` или `scp -r` каталога на VPS.
3. На сервере: `cd insta_download && cp .env.example .env` — пропишите **`BOT_TOKEN`**, **`TELEGRAM_CHANNEL_ID`**. Для Instagram: либо **`YTDLP_COOKIEFILE`** и файл `data/instagram_cookies.txt` (volume в `docker-compose` раскомментируйте при необходимости), либо вход через Firefox на VPS (**раздел «Instagram и VPS»** и `YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/...`).
4. Запуск: `docker compose up --build -d`. Логи: `docker compose logs -f bot` или `./logs/app.log`.
5. **Деплой с Mac:** `bash deploy/deploy.sh` — rsync **не перезаписывает** `.env` на VPS и **не удаляет** `data/firefox-ig/` (профиль Firefox для Instagram); остальное — как раньше.
6. **Файрвол:** при необходимости откройте только `PUBLIC_HEALTH_PORT` (если health смотрит наружу); для Telegram исходящий HTTPS достаточно по умолчанию.
7. Обновление: `git pull && docker compose up --build -d`.

Переменные **`VPS_*`** (хост, пользователь, порт, ключ или пароль) см. в **`.env.example`**: они **не используются** приложением `videobot`, только вашими будущими скриптами деплоя; пароль в `.env` хранить нежелательно — предпочтительнее **`VPS_SSH_KEY_PATH`**.

## Instagram и VPS
Ссылка вроде [этого Reel](https://www.instagram.com/reel/DYF4vdJRn_A/) в браузере без логина часто показывает только страницу входа; с сервера yt-dlp видит то же самое и пишет про ограничение аудитории.

### Вход в Instagram на VPS (Firefox в браузере)
Чтобы один раз залогиниться на сервере и дать боту доступ к cookies профиля:

1. На VPS в каталоге проекта: `docker compose --profile ig-login up -d ig-firefox` (образ подтянется при первом запуске).
2. **Не открывайте** веб-интерфейс в интернет: в `docker-compose.yml` порт привязан к `127.0.0.1` на сервере. С вашего компьютера:  
   `ssh -L 3100:127.0.0.1:3100 user@ваш-vps`  
   затем в локальном браузере откройте `http://localhost:3100` — появится Firefox на VPS.
3. В этом Firefox зайдите на [instagram.com](https://www.instagram.com) и войдите в аккаунт (2FA — как обычно в браузере).  
   Если после деплоя профиль «не сохраняется», на VPS один раз выполните: `sudo chown -R 1000:1000 data/firefox-ig` и перезапустите `ig-firefox` (`docker compose --profile ig-login restart ig-firefox`), затем снова войдите в Instagram.
4. На **Mac** (из корня репозитория, с рабочим SSH в `.env`):  
   `bash deploy/apply_vps_instagram_firefox_env.sh` — на VPS в `.env` запишется `YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/...` и перезапустится контейнер `bot`.  
   Либо вручную на VPS: `sh scripts/ig_firefox_profile_hint.sh` и вставьте строку в `.env`, затем `docker compose up -d bot`.
5. Сервис браузера можно остановить: `docker compose --profile ig-login stop ig-firefox` — профиль остаётся в `./data/firefox-ig`.

Учитывайте правила Instagram и риски хранения сессии на сервере; не пробрасывайте порт Firefox на `0.0.0.0` без VPN и сильной необходимости.

**Что ещё помогает:**
1. **Локально на Mac:** `YTDLP_COOKIES_FROM_BROWSER=chrome` — cookies из профиля Chrome (см. выше).
2. **`YTDLP_COOKIEFILE`** на VPS — файл **Netscape** `cookies.txt` ([инструкция yt-dlp](https://github.com/yt-dlp/yt-dlp#exporting-youtube-cookies)), права `600`, путь в `.env`.
3. **Резидентский прокси** — если Instagram режет датацентровые IP даже с cookies (реже, но бывает). Это уже настройка прокси для yt-dlp/системы, не вшита в бот по умолчанию.
4. **YouTube/Reddit** для регрессионных тестов — меньше зависимостей от логина.

Без Docker: на VPS можно `pip install -e .` и `systemd`; для контейнера см. разделы **Docker** и **Деплой на VPS** выше.

## Использование бота
- `/start`, `/help`, `/status`
- Сообщение, в котором есть ссылка `http(s)://…` (не обязательно в начале строки) — запуск загрузки и постинга в канал. Несколько запросов обрабатываются параллельно с ограничением `MAX_CONCURRENT_DOWNLOADS`.

## Линтинг
```bash
ruff check src
mypy src/videobot
```

## Стек
aiogram 3.x, aiohttp, pydantic-settings, yt-dlp, Docker.

## Troubleshooting
- **Бот не постит в канал**: добавьте бота администратором канала с правом публикации сообщений; проверьте `TELEGRAM_CHANNEL_ID`.
- **Instagram падает**: на Mac задайте `YTDLP_COOKIES_FROM_BROWSER=chrome` и войдите в Instagram в Chrome; на VPS — `YTDLP_COOKIEFILE` (см. README).
- **Превышен размер**: уменьшите `MAX_VIDEO_SIZE_MB` или лимиты Telegram (боты до ~50 МБ для видео).
- **Видео в Telegram «замирает», звук есть**: по умолчанию `TELEGRAM_REENCODE_MP4=true` — перекодировка в H.264 yuv420p + faststart; нужен `ffmpeg` в PATH. Отключение: `TELEGRAM_REENCODE_MP4=false`.
- **ffmpeg**: для перекодировки и для yt-dlp при склейке DASH должен быть в `PATH` (в Docker образе уже есть).

## Архитектура
Исходный код пакета: `src/videobot/` (модули `config`, `logging_setup`, `validators`, `downloaders`, `telegram_bot`, `publisher`, `cleanup_manager`, `app_lifecycle`). Подробнее: `ARCHITECTURE.md`.

## Non-goals
TikTok/Twitter, БД, веб-интерфейс админки бота, хранение видео после публикации — см. исходный README в истории спецификации.
