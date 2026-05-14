# Architecture

## Overview
This architecture defines a modular Python asynchronous Telegram bot that downloads videos from Instagram, YouTube, and Reddit upon receiving user URLs, processes them respecting size constraints, publishes to a configured Telegram channel, and manages cleanup and error handling robustly. The design ensures clear separation of concerns, uses asynchronous libraries like aiogram and aiohttp, employs pydantic-settings for configuration, and supports concurrency and retries robustly in a lightweight, deterministic monolith structure deployable with Docker.

## Components
### config
Load and manage application configuration from environment variables and .env files with validation.

Responsibilities:
- Define pydantic-settings models for structured config loading
- Load secrets and runtime parameters (e.g., MAX_VIDEO_SIZE_MB, Telegram token)
- Allow configuring retry logic, temp directory, log levels
- Expose config objects for use by other components
### logging_setup
Configure and initialize Python logging with structured logs and rotation as per settings.

Responsibilities:
- Setup root logger with handlers and formatters
- Log key system events, errors, and actions
- Support varying log verbosity levels
- Write logs to file and console following config
### validators
Validate and sanitize incoming URLs for supported platforms.

Responsibilities:
- Implement URL validation logic for Instagram, YouTube, Reddit video URLs
- Reject unsupported or malformed URLs early
- Provide descriptive error feedback for invalid URLs
### downloaders
Abstract and handle video downloads asynchronously with retries and size checks.

Responsibilities:
- Define BaseDownloader abstract class with async download interface
- Implement InstagramDownloader, YouTubeDownloader, RedditDownloader using yt-dlp asynchronously
- Apply retry logic and timeout on downloads
- Use tempfile module to store video temporarily in temp/ directory
- Validate and enforce MAX_VIDEO_SIZE_MB constraint before completing download
- Raise clear exceptions on failure for upstream error handling
### telegram_bot
Telegram bot interface using aiogram to receive URLs, respond to commands, and provide feedback.

Responsibilities:
- Implement /start, /help, /status commands
- Handle user messages containing URLs
- Validate URLs via validators component
- Trigger appropriate downloader based on URL parsing
- Process downloads concurrently using asyncio tasks
- Publish validated videos asynchronously to configured Telegram channel
- Notify user on success, failure, or ongoing processing states
- Implement graceful error handling and user notifications
### publisher
Publish downloaded video files asynchronously to the specified Telegram channel.

Responsibilities:
- Accept validated video files from downloaders
- Publish to Telegram channel asynchronously using aiogram
- Respect file size limits before publishing
- Ensure upload failures trigger user notification and possible retries
### cleanup_manager
Ensure robust and guaranteed removal of temporary files after processing.

Responsibilities:
- Monitor lifecycle of downloaded temp files
- Remove files upon success or failure reliably
- Use context managers or finalizers to safeguard cleanup
- Prevent orphaned temp files on errors or interruptions
### app_lifecycle
Manage application startup, graceful shutdown, and healthchecks.

Responsibilities:
- Initialize components at startup (config, logging, bot)
- Handle graceful shutdown signals ensuring cleanup
- Expose simple healthcheck HTTP endpoint for container orchestration
- Coordinate lifecycle tasks for orderly resource management
### docker_setup
Containerize the app with all dependencies and volume mounts.

Responsibilities:
- Dockerfile specifying Python environment, dependencies, ffmpeg installation
- docker-compose.yml for orchestrating container, logs volume, environment injections
- Ensure .env usage inside container for secrets
- Expose ports for healthchecks and bot operation
- Optimize for lightweight and reproducible container builds

## Data Flow
- User sends URL to Telegram bot
- Bot validates URL format with validators
- Bot selects appropriate downloader based on URL domain
- Downloader asynchronously downloads video using yt-dlp into temp dir
- Downloader enforces size limit and retries on failure
- Downloader returns downloaded file path or error
- Publisher reads downloaded file and asynchronously uploads video to Telegram channel
- Bot notifies user of success or error with descriptive message
- Cleanup manager deletes temporary files after publishing or failure
- Logging captures every major step, error, and user interaction
- App lifecycle coordinates startup, graceful shutdown, and healthcheck responses
