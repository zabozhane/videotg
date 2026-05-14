class DownloadFailed(Exception):
    """Download could not be completed after retries."""

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class SizeExceededError(DownloadFailed):
    """File exceeded configured MAX_VIDEO_SIZE_MB."""
