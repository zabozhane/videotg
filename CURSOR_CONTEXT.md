# Cursor Context

## Project
- Name: Async Telegram Video Publisher Bot
- Stack: Python 3.12+, aiogram 3.x, yt-dlp, aiohttp, asyncio, python-dotenv, ffmpeg, Docker + docker-compose

## Architecture Summary
This architecture defines a modular Python asynchronous Telegram bot that downloads videos from Instagram, YouTube, and Reddit upon receiving user URLs, processes them respecting size constraints, publishes to a configured Telegram channel, and manages cleanup and error handling robustly. The design ensures clear separation of concerns, uses asynchronous libraries like aiogram and aiohttp, employs pydantic-settings for configuration, and supports concurrency and retries robustly in a lightweight, deterministic monolith structure deployable with Docker.

## Applied Skills
- telegram_bot (local_pack): Reusable engineering context pack with: architecture, pitfalls, rules.
- python_async (local_pack): Reusable engineering context pack with: pitfalls, rules.

## MCP Recommendations
- Telegram Bot API docs/search MCP for quick endpoint lookup.
- HTTP inspection tools (e.g. curl/httpie workflows) to debug webhook/polling flows.
- Python docs MCP (asyncio section) for event-loop and coroutine references.
- Package index/search MCP to compare async-ready libraries before adoption.
- Ruff + pytest tooling context for fast local feedback loops.

## Current Task Backlog
- T1: Define project folder structure
- T2: Implement configuration loading with pydantic-settings
- T3: Setup Python logging
- T4: Implement URL validators for Instagram, YouTube, Reddit
- T5: Design BaseDownloader abstraction
- T6: Implement InstagramDownloader using yt-dlp asynchronously
- T7: Implement YouTubeDownloader using yt-dlp asynchronously
- T8: Implement RedditDownloader using yt-dlp asynchronously
- T9: Implement cleanup_manager for temporary files
- T10: Implement Telegram bot commands and URL message handling
- T11: Implement asynchronous download processing with concurrency
- T12: Implement publisher module to upload videos to Telegram channel
- T13: Integrate downloaders with publisher and cleanup
- T14: Implement app lifecycle management with graceful shutdown and healthcheck endpoint
- T15: Setup Dockerfile with base image, dependencies, ffmpeg, and entrypoint
- T16: Create docker-compose.yml including environment injection and log volume
- T17: Add typing and pydantic data models throughout the codebase
- T18: Add linting configuration and .gitignore file
- T19: Write README with comprehensive setup, usage, config, docker, and troubleshooting instructions
