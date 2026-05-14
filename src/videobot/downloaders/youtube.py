from videobot.downloaders.base import BaseDownloader


class YouTubeDownloader(BaseDownloader):
    def _ytdlp_format_selector(self) -> str:
        return "bestvideo+bestaudio/best"
