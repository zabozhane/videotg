# Workflow Report

## Quality Score
- Score: 80/100

## Inputs
- Idea: Ты — senior backend engineer и DevOps architect. Нужно реализовать production-ready Telegram-бота на Python.

Задача

Создать Telegram-бота, который:

1. Принимает URL от пользователя:
    * Instagram Reels / Posts
    * YouTube Shorts / Videos
    * Reddit videos
2. Автоматически:
    * скачивает видео во временную директорию
    * НЕ хранит видео постоянно
    * после успешной публикации удаляет временные файлы
    * публикует видео в заданный Telegram-канал
3. Бот должен:
    * работать асинхронно
    * обрабатывать несколько ссылок одновременно
    * поддерживать retry при ошибках
    * логировать ошибки и действия
    * валидировать URL
    * ограничивать размер видео
    * корректно обрабатывать приватные/недоступные видео

⸻

Технические требования

Стек

Использовать:

* Python 3.12+
* aiogram 3.x
* yt-dlp
* aiohttp
* asyncio
* python-dotenv
* ffmpeg (если нужен post-processing)
* Docker + docker-compose

⸻

Архитектура

Сделать чистую production-ready архитектуру:

project/
├── app/
│   ├── bot/
│   ├── services/
│   ├── downloaders/
│   ├── handlers/
│   ├── middlewares/
│   ├── utils/
│   ├── config/
│   └── main.py
├── temp/
├── logs/
├── .env
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md

⸻

ВАЖНО: безопасность и конфигурация

НИКАКИЕ ключи, токены и ID НЕ должны храниться в коде.

Все секреты должны быть вынесены в:

* .env
* environment variables

Использовать pydantic-settings или dotenv для загрузки конфигурации.

Пример:

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHANNEL_ID=
MAX_VIDEO_SIZE_MB=
TEMP_DIR=
LOG_LEVEL=

Никаких хардкодов.

⸻

Функциональность

Telegram бот

Команды:

* /start
* /help
* /status

Поведение:

* пользователь отправляет URL
* бот отвечает:
    * “Видео обрабатывается…”
* скачивает видео
* публикует в канал
* отправляет статус:
    * успешно
    * ошибка

⸻

Downloader layer

Сделать отдельный abstraction layer:

BaseDownloader

Реализации:

* InstagramDownloader
* YouTubeDownloader
* RedditDownloader

Использовать yt-dlp.

Система должна легко расширяться под TikTok/Twitter позже.

⸻

Работа с файлами

ВАЖНО:

* видео хранить ТОЛЬКО временно
* использовать tempfile
* после upload:
    * удалить файл
    * очистить temp directory
* реализовать cleanup even on exception

⸻

Ограничения

* ограничение размера видео
* timeout на скачивание
* retry policy
* graceful error handling

⸻

Логирование

Использовать logging.

Логировать:

* входящие URL
* начало скачивания
* успешную публикацию
* ошибки
* cleanup temp files

⸻

Docker

Сделать:

* Dockerfile
* docker-compose.yml

Контейнер должен:

* запускаться одной командой
* иметь ffmpeg
* использовать volume для logs

⸻

README

README должен содержать:

* установку
* запуск
* настройку .env
* docker setup
* примеры использования
* troubleshooting

⸻

Дополнительно

Реализовать:

* typing
* dataclasses/pydantic models
* linting recommendations
* .gitignore
* healthcheck
* structured config
* graceful shutdown

⸻

Что нужно сгенерировать

Сгенерируй полностью:

1. Архитектуру проекта
2. Все основные файлы
3. Полный код
4. Docker setup
5. requirements.txt
6. .env.example
7. README.md
8. Примеры конфигурации
9. Лучшие практики безопасности
10. Cleanup logic временных файлов
11. Асинхронную обработку
12. Обработку ошибок

Код должен быть production-ready, чистый и масштабируемый.
- Preferred stack: Python 3.12, aiogram 3.x, yt-dlp, aiohttp, asyncio, python-dotenv, ffmpeg, Docker + docker-compose
- Constraints:
- Use asynchronous code with asyncio and aiohttp
- Store secrets only in .env or environment variables (no hardcoding)
- Implement retry logic on download failures
- Limit downloaded video size (configurable)
- Use tempfile for temporary storage and ensure cleanup on success and errors
- Log all key events and errors using logging module
- Validate incoming URLs before processing
- Support concurrent processing of multiple links
- Provide graceful error handling and user feedback in bot
- Use pydantic-settings or dotenv for configuration loading

## Checks
- component_task_coverage: FAIL — No explicit task coverage for components: docker_setup
- task_dependency_integrity: PASS — All task dependencies reference known task IDs.
- constraint_signal: PASS — Constraints are represented in architecture/tasks text.
- overengineering_guard: PASS — No overengineering terms detected outside requested scope.

## Warnings
- None

## Output Summary
- Components: 9
- Tasks: 19
- Skills: 2