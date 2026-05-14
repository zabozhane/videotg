from videobot.config.settings import Settings
from videobot.downloaders.base import BaseDownloader
from videobot.downloaders.instagram import InstagramDownloader
from videobot.downloaders.reddit import RedditDownloader
from videobot.downloaders.youtube import YouTubeDownloader
from videobot.validators.urls import VideoPlatform


def downloader_for_platform(platform: VideoPlatform, settings: Settings) -> BaseDownloader:
    if platform is VideoPlatform.INSTAGRAM:
        return InstagramDownloader(settings)
    if platform is VideoPlatform.YOUTUBE:
        return YouTubeDownloader(settings)
    if platform is VideoPlatform.REDDIT:
        return RedditDownloader(settings)
    raise ValueError(f"Unknown platform: {platform}")
