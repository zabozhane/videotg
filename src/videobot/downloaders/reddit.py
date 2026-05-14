from videobot.downloaders.base import BaseDownloader


class RedditDownloader(BaseDownloader):
    def _ytdlp_format_selector(self) -> str:
        return "bestvideo+bestaudio/best"
