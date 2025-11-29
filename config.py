"""Configuration management for Suno Downloader."""

import os
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class SunoConfig:
    """Configuration class for Suno Downloader."""
    
    # API Configuration
    BASE_API_URL: str = "https://studio-api.prod.suno.com/api/feed/v2"
    PLAYLIST_API_URL: str = "https://studio-api.prod.suno.com/api/playlist/me"
    
    # File Configuration
    DEFAULT_DOWNLOAD_DIR: str = "suno-downloads"
    DEFAULT_TOKEN_FILE: str = "token.txt"
    DEFAULT_PLAYLIST_INDEX: str = "playlist_index.json"
    
    # Download Configuration
    DEFAULT_TIMEOUT: int = 30
    DEFAULT_THREADS: int = 4  # Default number of download threads
    CHUNK_SIZE: int = 8192
    MAX_FILENAME_LENGTH: int = 200
    MIN_TOKEN_SIZE: int = 500
    
    # Rate Limiting
    PAGE_DELAY: float = 5.0
    REQUEST_DELAY: float = 1.0
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    
    # File Patterns
    FILENAME_BAD_CHARS: str = r'[<>:"/\\|?*\x00-\x1F]'
    
    @classmethod
    def from_env(cls) -> 'SunoConfig':
        """Create configuration from environment variables."""
        return cls(
            DEFAULT_DOWNLOAD_DIR=os.getenv('SUNO_DOWNLOAD_DIR', cls.DEFAULT_DOWNLOAD_DIR),
            DEFAULT_TOKEN_FILE=os.getenv('SUNO_TOKEN_FILE', cls.DEFAULT_TOKEN_FILE),
            DEFAULT_TIMEOUT=int(os.getenv('SUNO_TIMEOUT', str(cls.DEFAULT_TIMEOUT))),
            DEFAULT_THREADS=int(os.getenv('SUNO_THREADS', str(cls.DEFAULT_THREADS))),
            MAX_RETRIES=int(os.getenv('SUNO_MAX_RETRIES', str(cls.MAX_RETRIES))),
        )


# Global configuration instance
config = SunoConfig.from_env()
