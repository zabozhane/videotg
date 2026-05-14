from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_channel_id: str = Field(
        ...,
        description="Target channel ID (@username or -100…)",
    )

    max_video_size_mb: float = Field(default=50.0, ge=0.1, le=2000.0)
    temp_dir: Path = Field(default=Path("temp"))
    log_dir: Path = Field(default=Path("logs"))
    log_level: str = Field(default="INFO")

    download_retries: int = Field(default=3, ge=1, le=10)
    download_timeout_seconds: float = Field(default=600.0, ge=30.0)
    upload_retries: int = Field(default=3, ge=1, le=10)
    max_concurrent_downloads: int = Field(default=3, ge=1, le=20)

    health_host: str = Field(default="0.0.0.0")
    health_port: int = Field(default=8080, ge=1, le=65535)

    log_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    log_backup_count: int = Field(default=5, ge=1, le=50)

    #: Netscape cookies.txt (see yt-dlp README). Strongly recommended for Instagram from a VPS.
    ytdlp_cookiefile: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("YTDLP_COOKIEFILE"),
    )

    #: e.g. "chrome" — yt-dlp reads cookies from the browser (local Mac + Instagram in Chrome).
    ytdlp_cookies_from_browser: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YTDLP_COOKIES_FROM_BROWSER"),
    )

    #: Re-encode to H.264 yuv420p + faststart for Telegram inline playback.
    telegram_reencode_mp4: bool = Field(
        default=True,
        validation_alias=AliasChoices("TELEGRAM_REENCODE_MP4"),
    )

    @field_validator("temp_dir", "log_dir", mode="before")
    @classmethod
    def coerce_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser() if not isinstance(v, Path) else v

    @field_validator("ytdlp_cookiefile", mode="before")
    @classmethod
    def optional_cookie_path(cls, v: str | Path | None) -> Path | None:
        if v is None or v == "":
            return None
        return Path(v).expanduser() if not isinstance(v, Path) else v

    @field_validator("ytdlp_cookies_from_browser", mode="before")
    @classmethod
    def optional_browser_cookies(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
