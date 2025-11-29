"""Utility functions for Suno Downloader."""

import os
import re
import time
import random
from typing import Optional, List, Dict, Any
from pathlib import Path

from config import config
from logger import logger
from exceptions import ConfigurationError


def sanitize_filename(name: str, maxlen: Optional[int] = None) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        name: The filename to sanitize
        maxlen: Maximum length for the filename
        
    Returns:
        Sanitized filename
    """
    if maxlen is None:
        maxlen = config.MAX_FILENAME_LENGTH
        
    safe = re.sub(config.FILENAME_BAD_CHARS, "_", name)
    safe = safe.strip(" .")
    return safe[:maxlen] if len(safe) > maxlen else safe


def get_unique_filename(filepath: str) -> str:
    """
    Generate a unique filename if the file already exists.
    
    Args:
        filepath: The desired file path
        
    Returns:
        Unique file path
    """
    if not os.path.exists(filepath):
        return filepath
        
    path = Path(filepath)
    name = path.stem
    suffix = path.suffix
    parent = path.parent
    
    counter = 2
    while True:
        new_filename = parent / f"{name} v{counter}{suffix}"
        if not os.path.exists(new_filename):
            return str(new_filename)
        counter += 1


def pick_proxy_dict(proxies_list: Optional[List[str]]) -> Optional[Dict[str, str]]:
    """
    Pick a random proxy from the list and format it for requests.
    
    Args:
        proxies_list: List of proxy URLs
        
    Returns:
        Proxy dictionary for requests or None
    """
    if not proxies_list:
        return None
        
    proxy = random.choice(proxies_list)
    return {"http": proxy, "https": proxy}


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Directory path to create
        
    Raises:
        ConfigurationError: If directory cannot be created
    """
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")
    except OSError as e:
        raise ConfigurationError(f"Cannot create directory {directory}: {e}")


def validate_token(token: str) -> bool:
    """
    Validate if a token looks like a valid JWT token.
    
    Args:
        token: Token string to validate
        
    Returns:
        True if token appears valid
    """
    if not token or len(token) < config.MIN_TOKEN_SIZE:
        return False
        
    # Basic JWT token validation (starts with "ey")
    return token.strip().startswith("ey")


def load_token_from_file(filepath: str) -> str:
    """
    Load token from a file with validation.
    
    Args:
        filepath: Path to token file
        
    Returns:
        Token string
        
    Raises:
        ConfigurationError: If token file is invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            token = f.read().strip()
            
        if not validate_token(token):
            raise ConfigurationError(f"Invalid token in file {filepath}")
            
        logger.info(f"Token loaded from {filepath}")
        return token
        
    except FileNotFoundError:
        raise ConfigurationError(f"Token file not found: {filepath}")
    except Exception as e:
        raise ConfigurationError(f"Error reading token file {filepath}: {e}")


def save_token_to_file(token: str, filepath: str) -> None:
    """
    Save token to a file with validation.
    
    Args:
        token: Token string to save
        filepath: Path to save token
        
    Raises:
        ConfigurationError: If token cannot be saved
    """
    if not validate_token(token):
        raise ConfigurationError("Invalid token format")
        
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(token)
        logger.info(f"Token saved to {filepath}")
    except Exception as e:
        raise ConfigurationError(f"Error saving token to {filepath}: {e}")


def rate_limit_delay(delay: float = None) -> None:
    """
    Apply rate limiting delay.
    
    Args:
        delay: Delay in seconds, uses config default if None
    """
    if delay is None:
        delay = config.REQUEST_DELAY
        
    if delay > 0:
        time.sleep(delay)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_info(filepath: str) -> Dict[str, Any]:
    """
    Get file information including size and modification time.
    
    Args:
        filepath: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': stat.st_mtime,
            'exists': True
        }
    except OSError:
        return {'exists': False}