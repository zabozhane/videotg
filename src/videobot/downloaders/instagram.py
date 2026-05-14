from videobot.downloaders.base import BaseDownloader


class InstagramDownloader(BaseDownloader):
    def _ytdlp_format_selector(self) -> str:
        return "bestvideo+bestaudio/best"
