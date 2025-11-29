"""Main downloader class for Suno tracks."""

import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from tqdm import tqdm

from config import config
from logger import logger
from exceptions import DownloadError, ConfigurationError
from utils import sanitize_filename, get_unique_filename, ensure_directory_exists
from api_client import SunoAPIClient
from metadata_handler import MetadataHandler


class SunoDownloader:
    """Main class for downloading Suno tracks."""
    
    def __init__(self, token: str, download_dir: str = None, 
                 proxies_list: Optional[List[str]] = None,
                 with_thumbnails: bool = False,
                 with_id_suffix: bool = False,
                 max_threads: int = None):
        """
        Initialize the downloader.
        
        Args:
            token: Authentication token
            download_dir: Directory to save downloads
            proxies_list: List of proxy URLs
            with_thumbnails: Whether to download and embed thumbnails
            with_id_suffix: Whether to append track ID suffix to filenames
        """
        self.token = token
        self.download_dir = download_dir or config.DEFAULT_DOWNLOAD_DIR
        self.proxies_list = proxies_list
        self.with_thumbnails = with_thumbnails
        self.with_id_suffix = with_id_suffix
        self.max_threads = max_threads or config.DEFAULT_THREADS
        
        # Initialize components
        self.api_client = SunoAPIClient(token, proxies_list)
        self.metadata_handler = MetadataHandler(token, proxies_list)
        
        # Ensure download directory exists
        ensure_directory_exists(self.download_dir)
        
        # Statistics
        self.stats = {
            'total_tracks': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': time.time(),
            'concurrent': 0  # Track concurrent downloads for progress bar positioning
        }
        
        # Thread safety
        self.stats_lock = threading.Lock()
        
        # Progress bars
        self.progress_lock = threading.Lock()
    
    def download_from_api(self, start_page: int = 1, end_page: Optional[int] = None,
                         liked_only: bool = True) -> Dict[str, Any]:
        """
        Download tracks directly from API.
        
        Args:
            start_page: Starting page number as shown in Suno UI (1-based)
            end_page: Ending page number as shown in Suno UI (None for all pages)
            liked_only: Whether to download only liked tracks
            
        Returns:
            Download statistics
        """
        logger.info(f"Starting download from API (pages {start_page}-{end_page or 'end'})")
        logger.info(f"Liked only: {liked_only}, Thumbnails: {self.with_thumbnails}, Threads: {self.max_threads}")
        
        try:
            # Get all tracks first to know total count
            all_tracks = list(self.api_client.get_all_tracks(start_page, end_page, liked_only))
            
            # Use ThreadPoolExecutor for concurrent downloads
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                # Submit all downloads to the executor
                futures = [executor.submit(self._download_single_track, track_data) for track_data in all_tracks]
                
                # Wait for all downloads to complete
                for future in futures:
                    # This will raise any exceptions that occurred during download
                    future.result()
                
        except KeyboardInterrupt:
            logger.warning("Download interrupted by user")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise DownloadError(f"API download failed: {e}")
        
        return self._get_final_stats()
    
    def download_from_index(self, index_file: str) -> Dict[str, Any]:
        """
        Download tracks from an index file.
        
        Args:
            index_file: Path to index file
            
        Returns:
            Download statistics
        """
        logger.info(f"Loading tracks from index file: {index_file}")
        
        try:
            tracks_data = self._load_index_file(index_file)
            
            logger.info(f"Downloading {len(tracks_data)} tracks using {self.max_threads} threads")
            
            # Use ThreadPoolExecutor for concurrent downloads
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                # Submit all downloads to the executor
                futures = [
                    executor.submit(self._download_single_track, track_data, track_id)
                    for track_id, track_data in tracks_data.items()
                ]
                
                # Wait for all downloads to complete
                for future in futures:
                    # This will raise any exceptions that occurred during download
                    future.result()
                
        except KeyboardInterrupt:
            logger.warning("Download interrupted by user")
        except Exception as e:
            logger.error(f"Index download failed: {e}")
            raise DownloadError(f"Index download failed: {e}")
        
        return self._get_final_stats()
    
    def create_index(self, index_file: str, start_page: int = 1, 
                    end_page: Optional[int] = None, liked_only: bool = True) -> Dict[str, Any]:
        """
        Create an index file of tracks without downloading.
        
        Args:
            index_file: Path to save index file
            start_page: Starting page number as shown in Suno UI (1-based)
            end_page: Ending page number as shown in Suno UI (None for all pages)
            liked_only: Whether to index only liked tracks
            
        Returns:
            Index creation statistics
        """
        logger.info(f"Creating index file: {index_file}")
        
        tracks = {}
        track_count = 0
        
        try:
            for track_data in self.api_client.get_all_tracks(start_page, end_page, liked_only):
                track_id = track_data.get('id')
                if track_id:
                    tracks[track_id] = track_data
                    track_count += 1
            
            # Create index data with metadata
            index_data = {
                "metadata": {
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_tracks": track_count,
                    "start_page": start_page,
                    "end_page": end_page if end_page else "end",
                    "liked_only": liked_only
                },
                "tracks": tracks
            }
            
            # Save index file
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Index file created with {track_count} tracks")
            return {"tracks_indexed": track_count, "index_file": index_file}
            
        except Exception as e:
            raise DownloadError(f"Index creation failed: {e}")
    
    def _download_single_track(self, track_data: Dict[str, Any], 
                              track_id: Optional[str] = None) -> None:
        """
        Download a single track with metadata.
        
        Args:
            track_data: Track information
            track_id: Track ID (optional, extracted from track_data if not provided)
        """
        # Thread-safe increment of total_tracks counter
        with self.stats_lock:
            self.stats['total_tracks'] += 1
        
        # Extract track information
        track_id = track_id or track_data.get('id')
        title = track_data.get('title') or track_id or 'Unknown'
        audio_url = track_data.get('audio_url')
        
        if not audio_url:
            logger.warning(f"No audio URL for track: {title}")
            with self.stats_lock:
                self.stats['skipped'] += 1
            return
        
        # Generate filename with optional track ID suffix (last 6 chars)
        safe_title = sanitize_filename(title)
        # Extract last 6 chars of track ID if enabled and available
        id_suffix = ""
        if self.with_id_suffix and track_id and len(track_id) >= 6:
            id_suffix = f"_{track_id[-6:]}"
        
        filename = f"{safe_title}{id_suffix}.mp3"
        filepath = os.path.join(self.download_dir, filename)
        
        # Check if the file with ID suffix already exists
        if os.path.exists(filepath):
            logger.info(f"Skipping: {title} (already downloaded as {filename})")
            with self.stats_lock:
                self.stats['skipped'] += 1
            return
            
        # Check for filename collisions with other tracks
        unique_filepath = get_unique_filename(filepath)
        
        logger.info(f"Processing: {title}")
        
        try:
            # Download the audio file with progress bar
            logger.debug(f"Downloading audio: {audio_url}")
            
            # Thread-safe increment for tracking progress bar position
            position = 0
            with self.stats_lock:
                self.stats['concurrent'] = (self.stats['concurrent'] + 1) % self.max_threads
                position = self.stats['concurrent']
            
            # Create a progress bar for this download
            pbar = tqdm(
                total=100, 
                desc=f"{os.path.basename(unique_filepath)}",
                unit="%",
                position=position,
                leave=False
            )
            
            # Callback to update the progress bar
            def update_progress(bytes_downloaded, total_size):
                if total_size > 0:
                    progress = min(100, int(100 * bytes_downloaded / total_size))
                    pbar.n = progress
                    pbar.refresh()
            
            try:
                # Download with progress tracking
                self.api_client.download_file(audio_url, unique_filepath, update_progress)
            finally:
                pbar.close()
            
            # Embed metadata
            self._embed_track_metadata(unique_filepath, track_data)
            
            # Log success
            if unique_filepath != filepath:
                logger.info(f"Downloaded as: {os.path.basename(unique_filepath)}")
            else:
                logger.info(f"Downloaded: {os.path.basename(unique_filepath)}")
            
            with self.stats_lock:
                self.stats['downloaded'] += 1
            
        except Exception as e:
            logger.error(f"Failed to download {title}: {e}")
            with self.stats_lock:
                self.stats['failed'] += 1
            
            # Clean up partial download
            if os.path.exists(unique_filepath):
                try:
                    os.remove(unique_filepath)
                except OSError:
                    pass
    
    def _embed_track_metadata(self, filepath: str, track_data: Dict[str, Any]) -> None:
        """
        Embed metadata into a downloaded track.
        
        Args:
            filepath: Path to the downloaded file
            track_data: Track metadata
        """
        try:
            metadata = track_data.get('metadata', {})
            track_id = track_data.get('id')
            
            self.metadata_handler.embed_metadata(
                mp3_path=filepath,
                title=track_data.get('title'),
                artist=track_data.get('display_name'),
                image_url=track_data.get('image_url') if self.with_thumbnails else None,
                prompt=metadata.get('prompt'),
                tags=metadata.get('tags'),
                track_id=track_id
            )
            
        except Exception as e:
            logger.warning(f"Failed to embed metadata for {filepath}: {e}")
            # Don't fail the download for metadata issues
    
    def _load_index_file(self, index_file: str) -> Dict[str, Any]:
        """
        Load tracks from an index file.
        
        Args:
            index_file: Path to index file
            
        Returns:
            Dictionary of track data
            
        Raises:
            ConfigurationError: If index file is invalid
        """
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Handle both new format (with metadata) and old format
            if isinstance(index_data, dict) and "tracks" in index_data:
                # New format with metadata
                metadata = index_data.get("metadata", {})
                if metadata:
                    logger.info(f"Index metadata: {metadata}")
                
                tracks = index_data["tracks"]
            else:
                # Old format (direct track dictionary)
                tracks = index_data
            
            logger.info(f"Loaded {len(tracks)} tracks from index file")
            return tracks
            
        except FileNotFoundError:
            raise ConfigurationError(f"Index file not found: {index_file}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in index file {index_file}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading index file {index_file}: {e}")
    
    def _get_final_stats(self) -> Dict[str, Any]:
        """Get final download statistics."""
        elapsed_time = time.time() - self.stats['start_time']
        
        stats = {
            **self.stats,
            'elapsed_time': elapsed_time,
            'success_rate': (self.stats['downloaded'] / max(self.stats['total_tracks'], 1)) * 100
        }
        
        logger.info(f"Download complete: {stats['downloaded']}/{stats['total_tracks']} tracks")
        logger.info(f"Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"Time elapsed: {elapsed_time:.1f} seconds")
        
        return stats
    
    def test_connection(self, page: int = 1, liked_only: bool = True) -> Dict[str, Any]:
        """
        Test API connection.
        
        Args:
            page: Page number to test as shown in Suno UI (1-based)
            liked_only: Whether to test with liked tracks only
            
        Returns:
            Test results
        """
        return self.api_client.test_connection(page, liked_only)
    
    def close(self):
        """Clean up resources."""
        if self.api_client:
            self.api_client.close()
        logger.info("Downloader closed")
