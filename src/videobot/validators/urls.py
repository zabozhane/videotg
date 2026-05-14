from __future__ import annotations

import re
from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class VideoPlatform(StrEnum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    REDDIT = "reddit"


class ValidatedUrl(BaseModel):
    url: str = Field(min_length=8)
    platform: VideoPlatform


_INSTAGRAM_HOSTS = frozenset({"instagram.com", "www.instagram.com", "m.instagram.com"})
_YOUTUBE_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"})
_REDDIT_HOSTS = frozenset({"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"})

_REEL_PATH = re.compile(r"^/(?:reel|reels|p|tv)/[\w-]+/?", re.I)
_YT_VIDEO = re.compile(r"^/(watch|shorts|live)(/|\?)", re.I)
_REDDIT_VIDEO = re.compile(r"^/r/[\w.-]+/comments/[\w]+", re.I)


def _host(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Нужна полная ссылка с http(s)://")
    return parsed.netloc.lower().split(":")[0]


def validate_video_url(raw: str) -> ValidatedUrl:
    text = raw.strip()
    if not text:
        raise ValueError("Пустая ссылка")

    # Take first URL-like token from a line
    for token in text.split():
        if token.startswith("http://") or token.startswith("https://"):
            text = token
            break

    host = _host(text)
    path = urlparse(text).path or "/"

    if host in _INSTAGRAM_HOSTS or host.endswith(".instagram.com"):
        if not _REEL_PATH.match(path) and "/p/" not in path and "/reel" not in path.lower():
            raise ValueError("Поддерживаются посты и Reels Instagram (путь /p/… или /reel/…)")
        return ValidatedUrl(url=text, platform=VideoPlatform.INSTAGRAM)

    if host == "youtu.be":
        if len(path) < 2:
            raise ValueError("Некорректная ссылка YouTube")
        return ValidatedUrl(url=text, platform=VideoPlatform.YOUTUBE)

    if host in _YOUTUBE_HOSTS:
        if not _YT_VIDEO.match(path) and "/watch" not in path:
            raise ValueError("Поддерживаются ролики и Shorts YouTube (watch, shorts, live)")
        return ValidatedUrl(url=text, platform=VideoPlatform.YOUTUBE)

    if host in _REDDIT_HOSTS or host.endswith(".reddit.com") or host == "v.reddit.com":
        if "reddit.com/gallery/" in text:
            raise ValueError("Галереи Reddit не поддерживаются, нужна ссылка на пост с видео")
        if not _REDDIT_VIDEO.match(path) and "/s/" not in path:
            raise ValueError("Нужна ссылка на пост Reddit с видео (/r/…/comments/…)")
        return ValidatedUrl(url=text, platform=VideoPlatform.REDDIT)

    raise ValueError("Поддерживаются только Instagram, YouTube и Reddit")
