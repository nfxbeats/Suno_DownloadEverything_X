"""API client for Suno services."""

import time
import os
from typing import Dict, List, Optional, Any, Iterator, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import config
from logger import logger
from exceptions import APIError, AuthenticationError
from utils import pick_proxy_dict, rate_limit_delay


class SunoAPIClient:
    """Client for interacting with Suno API."""
    
    def __init__(self, token: str, proxies_list: Optional[List[str]] = None):
        """
        Initialize the API client.
        
        Args:
            token: Authentication token
            proxies_list: List of proxy URLs
        """
        self.token = token
        self.proxies_list = proxies_list
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "SunoDownloader/2.0"
        })
        
        return session
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with error handling.
        
        Args:
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If request fails
        """
        try:
            # Apply rate limiting
            rate_limit_delay()
            
            # Set proxy if available
            if 'proxies' not in kwargs:
                kwargs['proxies'] = pick_proxy_dict(self.proxies_list)
            
            # Set timeout if not specified
            if 'timeout' not in kwargs:
                kwargs['timeout'] = config.DEFAULT_TIMEOUT
            
            logger.debug(f"Making request to: {url}")
            response = self.session.get(url, **kwargs)
            
            # Handle authentication errors
            if response.status_code in [401, 403]:
                raise AuthenticationError(
                    f"Authentication failed (status {response.status_code}). "
                    "Token may be expired or incorrect."
                )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
    
    def get_feed_page(self, page: int, liked_only: bool = True) -> Dict[str, Any]:
        """
        Get a page from the feed API.
        
        Args:
            page: Page number to fetch (1-based as displayed to users)
            liked_only: Whether to fetch only liked tracks
            
        Returns:
            API response data
        """
        # Convert from 1-based (UI) to 0-based (API)
        api_page = max(0, page - 1)
        
        params = {
            "page": api_page,
            "hide_disliked": "true",
            "hide_gen_stems": "true",
            "hide_studio_clips": "true"
        }
        
        if liked_only:
            params["is_liked"] = "true"
        
        url = f"{config.BASE_API_URL}?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        logger.info(f"Fetching feed page {page} (liked_only={liked_only})")
        response = self._make_request(url)
        return response.json()
    
    def get_playlist_page(self, page: int = 1) -> Dict[str, Any]:
        """
        Get a page from the playlist API.
        
        Args:
            page: Page number to fetch
            
        Returns:
            API response data
        """
        params = {
            "page": page,
            "show_trashed": "false",
            "show_sharelist": "false"
        }
        
        url = f"{config.PLAYLIST_API_URL}?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        logger.info(f"Fetching playlist page {page}")
        response = self._make_request(url)
        return response.json()
    
    def get_workspace_page(self, page: int = 1) -> Dict[str, Any]:
        """
        Get a page from the workspace (projects) API.
        
        Args:
            page: Page number to fetch
            
        Returns:
            API response data
        """
        params = {
            "page": page,
            "sort": "max_created_at_last_updated_clip",
            "show_trashed": "false"
        }
        
        url = f"{config.WORKSPACE_API_URL}?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        logger.info(f"Fetching workspace page {page}")
        response = self._make_request(url)
        return response.json()
    
    def get_workspace_by_id(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get a specific workspace by ID with all clips (handles pagination).
        
        Args:
            workspace_id: Workspace/project ID
            
        Returns:
            Workspace data including all clips from all pages
        """
        logger.info(f"Fetching workspace: {workspace_id}")
        
        all_clips = []
        page = 0
        workspace_data = None
        
        while True:
            # Use base project URL with pagination
            url = f"https://studio-api.prod.suno.com/api/project/{workspace_id}?page={page}"
            
            logger.debug(f"Fetching workspace {workspace_id} page {page}")
            response = self._make_request(url)
            data = response.json()
            
            # Store workspace metadata from first page
            if workspace_data is None:
                workspace_data = data.copy()
            
            # Extract clips from this page
            project_clips = data.get("project_clips", [])
            
            if not project_clips:
                logger.info(f"No more clips found on page {page} for workspace {workspace_id}")
                break
            
            logger.info(f"Found {len(project_clips)} clips on page {page} for workspace {workspace_id}")
            all_clips.extend(project_clips)
            
            page += 1
            
            # Apply page delay between requests
            if project_clips:  # Only delay if we got clips and might fetch more
                time.sleep(config.PAGE_DELAY)
        
        # Update the workspace data with all collected clips
        workspace_data["project_clips"] = all_clips
        logger.info(f"Total clips retrieved for workspace {workspace_id}: {len(all_clips)}")
        
        return workspace_data
    
    def get_all_workspaces(self) -> List[Dict[str, Any]]:
        """
        Get all workspaces (projects) from the API.
        
        Returns:
            List of workspace data dictionaries
        """
        all_workspaces = []
        page = 1
        
        while True:
            try:
                data = self.get_workspace_page(page)
                projects = data.get("projects", [])
                
                if not projects:
                    logger.info(f"No more workspaces found on page {page}")
                    break
                
                logger.info(f"Found {len(projects)} workspaces on page {page}")
                all_workspaces.extend(projects)
                
                page += 1
                
                # Apply page delay
                time.sleep(config.PAGE_DELAY)
                
            except APIError as e:
                logger.error(f"Failed to fetch workspace page {page}: {e}")
                break
        
        logger.info(f"Total workspaces retrieved: {len(all_workspaces)}")
        return all_workspaces
    
    def get_all_tracks(self, start_page: int = 1, end_page: Optional[int] = None, 
                      liked_only: bool = True) -> Iterator[Dict[str, Any]]:
        """
        Generator that yields all tracks from the feed.
        
        Args:
            start_page: Starting page number
            end_page: Ending page number (None for all pages)
            liked_only: Whether to fetch only liked tracks
            
        Yields:
            Track data dictionaries
        """
        page = start_page
        
        while end_page is None or page <= end_page:
            try:
                data = self.get_feed_page(page, liked_only)
                clips = data if isinstance(data, list) else data.get("clips", [])
                
                if not clips:
                    logger.info(f"No more clips found on page {page}")
                    break
                
                logger.info(f"Found {len(clips)} clips on page {page}")
                
                for clip in clips:
                    yield self._process_track_data(clip, page)
                
                page += 1
                
                # Apply page delay
                if page <= (end_page or float('inf')):
                    time.sleep(config.PAGE_DELAY)
                    
            except APIError as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break
    
    def _process_track_data(self, clip: Dict[str, Any], page: int) -> Dict[str, Any]:
        """
        Process raw track data from API response.
        
        Args:
            clip: Raw clip data from API
            page: Page number where track was found
            
        Returns:
            Processed track data
        """
        metadata_dict = clip.get("metadata", {})
        
        return {
            "id": clip.get("id"),
            "title": clip.get("title"),
            "audio_url": clip.get("audio_url"),
            "image_url": clip.get("image_url"),
            "display_name": clip.get("display_name"),
            "is_liked": clip.get("is_liked", False),
            "page": page,
            "metadata": {
                "prompt": metadata_dict.get("prompt"),
                "tags": metadata_dict.get("tags"),
                "duration": metadata_dict.get("duration"),
                "created_at": clip.get("created_at"),
            }
        }
    
    def download_file(self, url: str, filepath: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """
        Download a file from URL.
        
        Args:
            url: File URL to download
            filepath: Local path to save file
            progress_callback: Optional callback for progress updates (receives bytes_downloaded and total_size)
            
        Returns:
            Path to saved file
            
        Raises:
            APIError: If download fails
        """
        try:
            logger.info(f"Downloading: {url}")
            
            response = self._make_request(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=config.CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_downloaded, total_size)
            
            logger.info(f"Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            raise APIError(f"Download failed for {url}: {e}")
    
    def test_connection(self, page: int = 1, liked_only: bool = True) -> Dict[str, Any]:
        """
        Test API connection and return sample data.
        
        Args:
            page: Page number to test
            liked_only: Whether to test with liked tracks only
            
        Returns:
            Sample API response data
        """
        logger.info("Testing API connection...")
        return self.get_feed_page(page, liked_only)
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
            logger.debug("API client session closed")
