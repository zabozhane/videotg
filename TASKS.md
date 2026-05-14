# Implementation Tasks

## Status (2026-05-14)
Реализация в репозитории: пакет `src/videobot/`, Docker/compose, README. Проверки: `ruff check src`, `mypy src/videobot`. Сборка Docker не проверена в этой среде (daemon недоступен).

---

## T1 — Define project folder structure
Priority: high

Create the initial project folder structure with separate directories for config, downloaders, telegram_bot, validators, logging_setup, publisher, cleanup_manager, and app_lifecycle. Add __init__.py files where appropriate to enable package imports.

Depends on:
- None

## T2 — Implement configuration loading with pydantic-settings
Priority: high

Create configuration models using pydantic-settings for all needed settings including MAX_VIDEO_SIZE_MB, Telegram token, retry parameters, temp directory, and log levels. Load configuration from .env and environment variables. Expose a config instance usable throughout the project.

Depends on:
- T1

## T3 — Setup Python logging
Priority: high

Configure Python logging with structured log format, rotation, and configurable verbosity levels. Set up console and file handlers. Log key system events, errors, and actions as per config.

Depends on:
- T1
- T2

## T4 — Implement URL validators for Instagram, YouTube, Reddit
Priority: high

Develop URL validation logic to identify and validate URLs from Instagram Reels/Posts, YouTube Shorts/Videos, and Reddit videos. Provide meaningful error responses for invalid or unsupported URLs.

Depends on:
- T1

## T5 — Design BaseDownloader abstraction
Priority: high

Define an abstract BaseDownloader class with async download interface that enforces retry logic and timeout handling. Include method signatures and exceptions for derived downloaders to implement.

Depends on:
- T1
- T2

## T6 — Implement InstagramDownloader using yt-dlp asynchronously
Priority: high

Implement the InstagramDownloader subclass that downloads Instagram Reels/Posts asynchronously using yt-dlp with retries and respects timeout. Store downloads temporarily using tempfile module in the configured temp directory. Enforce MAX_VIDEO_SIZE_MB limit. Raise clear exceptions on failure.

Depends on:
- T5
- T2

## T7 — Implement YouTubeDownloader using yt-dlp asynchronously
Priority: high

Implement the YouTubeDownloader subclass that downloads YouTube Shorts/Videos asynchronously using yt-dlp with retries and timeout. Use tempfile for storing the downloaded file. Enforce size limit. Handle errors clearly.

Depends on:
- T5
- T2

## T8 — Implement RedditDownloader using yt-dlp asynchronously
Priority: high

Implement the RedditDownloader subclass that downloads Reddit videos asynchronously with retry and timeout logic, storing temporarily using tempfile. Enforce MAX_VIDEO_SIZE_MB. Provide clear exception handling.

Depends on:
- T5
- T2

## T9 — Implement cleanup_manager for temporary files
Priority: medium

Create cleanup manager module that handles guaranteed deletion of temporary files after download success or failure. Use context managers or finalizers to ensure no orphaned temp files remain in any exit path.

Depends on:
- T1

## T10 — Implement Telegram bot commands and URL message handling
Priority: high

Build Telegram bot using aiogram 3.x with /start, /help, /status commands. Handle incoming user messages containing URLs by validating them using validator module and passing valid URLs for download processing.

Depends on:
- T1
- T2
- T4
- T3

## T11 — Implement asynchronous download processing with concurrency
Priority: high

Integrate the downloader classes with the Telegram bot message handler to process downloads concurrently using asyncio tasks for multiple user requests.

Depends on:
- T6
- T7
- T8
- T10

## T12 — Implement publisher module to upload videos to Telegram channel
Priority: high

Develop the publisher module to asynchronously publish downloaded video files to the specified Telegram channel using aiogram. Check file size limits before uploading and handle upload failures with retries and user notification.

Depends on:
- T2
- T3

## T13 — Integrate downloaders with publisher and cleanup
Priority: high

Tie together the downloader output with the publisher module to upload videos after successful download, and invoke cleanup_manager to delete temporary files after success or error. Ensure user notifications on success or failure.

Depends on:
- T9
- T11
- T12

## T14 — Implement app lifecycle management with graceful shutdown and healthcheck endpoint
Priority: medium

Create startup and shutdown handlers to initialize configuration, logging, and bot. Implement graceful shutdown sequencing including cleanup of active tasks. Provide a lightweight HTTP healthcheck endpoint for container orchestration.

Depends on:
- T2
- T3
- T10

## T15 — Setup Dockerfile with base image, dependencies, ffmpeg, and entrypoint
Priority: medium

Create Dockerfile that installs Python 3.12+, project dependencies, ffmpeg binaries, sets up working directory, copies source code, configures environment, and sets entrypoint to start the bot and lifecycle management.

Depends on:
- T1
- T2

## T16 — Create docker-compose.yml including environment injection and log volume
Priority: medium

Build docker-compose configuration to launch the bot container with .env file, volumes for logs, expose healthcheck port, and define restart policies. Document in README how to build and run containers.

Depends on:
- T15

## T17 — Add typing and pydantic data models throughout the codebase
Priority: medium

Enhance all modules with proper Python typing annotations and use pydantic data models for structured data passing where applicable for validation and clarity.

Depends on:
- T1

## T18 — Add linting configuration and .gitignore file
Priority: low

Configure linting tools (e.g. flake8, black, mypy) for the project and create a .gitignore file to exclude virtual environments, __pycache__, .env, temp files, and docker artifacts.

Depends on:
- T1

## T19 — Write README with comprehensive setup, usage, config, docker, and troubleshooting instructions
Priority: low

Compose README documentation explaining how to setup environment variables, run the bot locally and via Docker, usage instructions for the Telegram bot, configuration options, logging info, and common troubleshooting tips.

Depends on:
- T1
- T2
- T15
- T16

