"""Custom exceptions for Suno Downloader."""


class SunoDownloaderError(Exception):
    """Base exception for Suno Downloader."""
    pass


class AuthenticationError(SunoDownloaderError):
    """Raised when authentication fails."""
    pass


class APIError(SunoDownloaderError):
    """Raised when API requests fail."""
    pass


class DownloadError(SunoDownloaderError):
    """Raised when file download fails."""
    pass


class MetadataError(SunoDownloaderError):
    """Raised when metadata embedding fails."""
    pass


class ConfigurationError(SunoDownloaderError):
    """Raised when configuration is invalid."""
    pass


class TokenError(SunoDownloaderError):
    """Raised when token operations fail."""
    pass