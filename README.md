# Async Telegram Video Publisher Bot

Telegram-бот на Python: по ссылке асинхронно скачивает видео с **Instagram**, **YouTube** и **Reddit** (yt-dlp), при необходимости перекодирует для клиентов Telegram, публикует в заданный канал и удаляет временные файлы.

## Возможности

- Команды `/start`, `/help`, `/status`
- Одна ссылка в сообщении — отдельный фоновый пайплайн (скачивание → перекодирование → публикация)
- Несколько ссылок подряд: до **`MAX_CONCURRENT_DOWNLOADS`** (по умолчанию 3) обрабатываются параллельно, остальные ждут в очереди
- Статус в чате: «Принял ссылку…», после скачивания — «Скачивание завершено…», в конце — «Готово: видео отправлено в канал»
- Health HTTP: `GET /health` → `{"status":"ok"}`

## Требования

- Python **3.12+**
- [ffmpeg](https://ffmpeg.org/) (склейка DASH у yt-dlp и перекодирование для Telegram)
- Токен бота ([@BotFather](https://t.me/BotFather)) и права бота на публикацию в канале

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

Обязательные переменные: **`BOT_TOKEN`**, **`TELEGRAM_CHANNEL_ID`** (`@channel` или `-100…`). Полный список — в [`.env.example`](.env.example).

## Переменные окружения (основные)

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `MAX_VIDEO_SIZE_MB` | 50 | Лимит размера файла |
| `MAX_CONCURRENT_DOWNLOADS` | 3 | Параллельных загрузок (1–20) |
| `DOWNLOAD_TIMEOUT_SECONDS` | 600 | Таймаут одной попытки yt-dlp |
| `TELEGRAM_REENCODE_MP4` | true | H.264 + AAC + faststart для Telegram |
| `TELEGRAM_SEND_VIDEO_TIMEOUT_SECONDS` | 3600 | Таймаут одного `sendVideo` (медленный uplink VPS) |
| `TELEGRAM_API_SESSION_TIMEOUT_SECONDS` | 180 | Таймаут aiohttp-сессии бота (long polling + загрузки) |
| `YTDLP_COOKIES_FROM_BROWSER` | — | Cookies из браузера, напр. `chrome` или `firefox:/path/to/profile` |
| `YTDLP_COOKIEFILE` | — | Netscape `cookies.txt` ([FAQ yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)) |

Переменные **`VPS_*`** в `.env.example` нужны только скриптам деплоя, не приложению.

## Instagram: cookies

### Локально (macOS) — Chrome

1. Войдите на [instagram.com](https://www.instagram.com) в **Chrome**.
2. В `.env`: `YTDLP_COOKIES_FROM_BROWSER=chrome`.
3. Перезапустите бота.

При первом доступе к Keychain разрешите чтение cookies.

### Локально — файл `cookies.txt`

Экспорт Netscape (расширение **Get cookies.txt LOCALLY** в Chrome и т.п.) → путь в **`YTDLP_COOKIEFILE`**. Если не используете Chrome, уберите **`YTDLP_COOKIES_FROM_BROWSER`**.

### VPS — Firefox в Docker (`ig-login`)

1. `docker compose --profile ig-login up -d ig-firefox`
2. SSH-туннель: `ssh -L 3100:127.0.0.1:3100 user@vps` → `http://localhost:3100`
3. Войдите в Instagram в этом Firefox.
4. На Mac: `bash deploy/apply_vps_instagram_firefox_env.sh` (пропишет `YTDLP_COOKIES_FROM_BROWSER=firefox:/igfirefox/...` на VPS и перезапустит `bot`).

Профиль хранится в `./data/firefox-ig`. При проблемах с записью: `sudo chown -R 1000:1000 data/firefox-ig`.

### VPS — как бот использует cookies

Для **Instagram** бот:

1. Читает cookies из Firefox (профиль из `YTDLP_COOKIES_FROM_BROWSER`), при блокировке БД — копирует `cookies.sqlite` во временный каталог.
2. Сохраняет их в Netscape-файл для yt-dlp (нужен **`sessionid`**).
3. Если задан **`YTDLP_COOKIEFILE`**, подмешивает файл, но при конфликте **приоритет у браузера** (свежий логин на VPS не затирается старым `cookies.txt`).

В логах: `Instagram: cookies → … sessionid=True/False`. Если `False` — снова войдите в Instagram в Firefox на VPS.

Без логина Instagram с VPS часто отвечает «login required» даже при корректной ссылке.

## Docker

```bash
cp .env.example .env
# BOT_TOKEN, TELEGRAM_CHANNEL_ID; на VPS — cookies (см. выше)
docker compose up --build -d
```

- **Health:** с хоста `curl -s http://127.0.0.1:${PUBLIC_HEALTH_PORT:-8080}/health`
- **Логи:** `./logs`, **temp:** том `bot_temp`
- **Firefox-профиль:** `./data/firefox-ig:/igfirefox:ro` у сервиса `bot`
- Опционально: `YTDLP_COOKIEFILE=/run/instagram_cookies.txt` + volume к файлу (см. комментарии в `docker-compose.yml`)

Сервис `ig-firefox` — только с профилем `ig-login`, порт **127.0.0.1:3100** на VPS.

## Деплой на VPS

**С Mac (из корня репозитория, `.env` с `VPS_HOST`, `VPS_USER`, ключ или пароль):**

```bash
bash deploy/deploy.sh
```

- Rsync проекта на сервер (**не перезаписывает** `.env` на VPS, **не удаляет** `data/firefox-ig/`)
- `docker compose up --build -d` на сервере

**Диагностика без деплоя:**

```bash
bash deploy/diag.sh
```

Показывает `docker compose ps` и последние ~200 строк логов `bot`.

**Обновление вручную на сервере:** `git pull && docker compose up --build -d`

Предпочтительно **`VPS_SSH_KEY_PATH`**, не пароль в `.env`.

## Использование

Отправьте боту сообщение со ссылкой `https://…` (Instagram Reels/пост, YouTube, Reddit с видео).

- Не обязательно ждать окончания предыдущей ссылки — можно слать несколько; лишние встанут в очередь после лимита параллелизма.
- Не дублируйте **ту же** ссылку, пока не пришло «Готово» или ошибка.
- Instagram на VPS часто **1–5+ минут** (DASH + ffmpeg + загрузка в Telegram).

## Линтинг

```bash
ruff check src
mypy src/videobot
```

## Стек

aiogram 3.x, aiohttp, pydantic-settings, yt-dlp, Docker (python:3.12-slim + ffmpeg).

## Troubleshooting

| Симптом | Что проверить |
|---------|----------------|
| Не постит в канал | Бот — админ канала с правом публикации; `TELEGRAM_CHANNEL_ID` |
| Instagram: login required | `sessionid=False` в логах; перелогин в Firefox на VPS; актуальный `YTDLP_COOKIEFILE` |
| Долго «висит» после ссылки | Нормально на этапе ffmpeg/отправки; смотрите логи `Отправка в канал` / `Published` |
| Нет ответа бота, но `/health` ok | Раньше — таймаут getUpdates (~60 с); сейчас `TELEGRAM_API_SESSION_TIMEOUT_SECONDS=180`; перезапуск после деплоя |
| Docker `unhealthy` | При нагрузке ffmpeg healthcheck мог не успевать; в compose увеличены интервалы; `bash deploy/diag.sh` |
| Файл слишком большой | `MAX_VIDEO_SIZE_MB`; лимит Telegram для ботов ~50 МБ на видео |
| Видео в Telegram без картинки | `TELEGRAM_REENCODE_MP4=true`, ffmpeg в PATH; отключение: `false` (риск несовместимого кодека) |
| Ошибка загрузки в канал | `TELEGRAM_SEND_VIDEO_TIMEOUT_SECONDS`; uplink VPS; логи `Upload attempt … failed` |

## Архитектура

Код: `src/videobot/` — `config`, `downloaders`, `telegram_bot`, `publisher`, `cleanup_manager`, `app_lifecycle`. Подробнее: [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Non-goals

TikTok/Twitter, БД, веб-админка, долговременное хранение видео после публикации.
