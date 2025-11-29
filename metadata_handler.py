"""Metadata handling for audio files."""

from typing import Optional
import requests
from mutagen.id3 import ID3, APIC, TIT2, TPE1, USLT, COMM, TXXX, error
from mutagen.id3 import TXXX as PROMPT  # Using TXXX as a custom frame for PROMPT
from mutagen.mp3 import MP3

from config import config
from logger import logger
from exceptions import MetadataError
from utils import pick_proxy_dict


class MetadataHandler:
    """Handler for embedding metadata into audio files."""
    
    def __init__(self, token: Optional[str] = None, proxies_list: Optional[list] = None):
        """
        Initialize metadata handler.
        
        Args:
            token: Authentication token for image downloads
            proxies_list: List of proxy URLs
        """
        self.token = token
        self.proxies_list = proxies_list
    
    def embed_metadata(self, mp3_path: str, title: Optional[str] = None,
                      artist: Optional[str] = None, image_url: Optional[str] = None,
                      prompt: Optional[str] = None, tags: Optional[str] = None,
                      track_id: Optional[str] = None) -> None:
        """
        Embed metadata into an MP3 file.
        
        Args:
            mp3_path: Path to MP3 file
            title: Track title
            artist: Artist name
            image_url: URL to cover art image
            prompt: AI generation prompt
            tags: Track tags
            track_id: Unique track identifier
            
        Raises:
            MetadataError: If metadata embedding fails
        """
        try:
            logger.debug(f"Embedding metadata for: {mp3_path}")
            
            # Load the MP3 file
            audio = MP3(mp3_path, ID3=ID3)
            
            # Add ID3 tags if they don't exist
            try:
                audio.add_tags()
            except error:
                pass  # Tags already exist
            
            # Embed basic metadata
            if title:
                audio.tags["TIT2"] = TIT2(encoding=3, text=title)
                logger.debug(f"Added title: {title}")
            
            if artist:
                audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
                logger.debug(f"Added artist: {artist}")
            
            # Embed prompt as unsynchronized lyrics
            if prompt:
                audio.tags["USLT"] = USLT(encoding=3, lang="eng", desc="Prompt", text=prompt)
                logger.debug("Added prompt as lyrics")
            
            # Embed tags as custom PROMPT field
            if tags:
                audio.tags["TXXX:PROMPT"] = PROMPT(
                    encoding=3,
                    desc="PROMPT",
                    text=tags
                )
                logger.debug("Added tags as PROMPT")
            
            # Embed track ID as custom field
            if track_id:
                audio.tags["TXXX:TRACKID"] = TXXX(
                    encoding=3,
                    desc="TrackID",
                    text=track_id
                )
                logger.debug(f"Added track ID: {track_id}")
            
            # Embed cover art if URL provided
            if image_url:
                self._embed_cover_art(audio, image_url)
            
            # Save the changes
            audio.save(v2_version=3)
            logger.info(f"Metadata embedded successfully: {mp3_path}")
            
        except Exception as e:
            raise MetadataError(f"Failed to embed metadata for {mp3_path}: {e}")
    
    def _embed_cover_art(self, audio: MP3, image_url: str) -> None:
        """
        Download and embed cover art into the audio file.
        
        Args:
            audio: MP3 audio object
            image_url: URL to cover art image
            
        Raises:
            MetadataError: If cover art embedding fails
        """
        try:
            logger.debug(f"Downloading cover art: {image_url}")
            
            # Set up headers and proxy
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            proxy_dict = pick_proxy_dict(self.proxies_list)
            
            # Download the image
            response = requests.get(
                image_url,
                proxies=proxy_dict,
                headers=headers,
                timeout=config.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            image_bytes = response.content
            mime_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
            
            # Remove existing cover art
            for key in list(audio.tags.keys()):
                if key.startswith("APIC"):
                    del audio.tags[key]
            
            # Add new cover art
            audio.tags.add(APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # Cover (front)
                desc="Cover",
                data=image_bytes
            ))
            
            logger.debug("Cover art embedded successfully")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to download cover art from {image_url}: {e}")
            # Don't raise exception for cover art failures
        except Exception as e:
            logger.warning(f"Failed to embed cover art: {e}")
            # Don't raise exception for cover art failures
    
    def get_metadata(self, mp3_path: str) -> dict:
        """
        Extract metadata from an MP3 file.
        
        Args:
            mp3_path: Path to MP3 file
            
        Returns:
            Dictionary containing metadata
            
        Raises:
            MetadataError: If metadata extraction fails
        """
        try:
            audio = MP3(mp3_path, ID3=ID3)
            
            metadata = {}
            
            if audio.tags:
                # Extract basic metadata
                if "TIT2" in audio.tags:
                    metadata["title"] = str(audio.tags["TIT2"])
                
                if "TPE1" in audio.tags:
                    metadata["artist"] = str(audio.tags["TPE1"])
                
                if "USLT" in audio.tags:
                    metadata["prompt"] = str(audio.tags["USLT"])
                
                # Extract tags from PROMPT field
                for key in audio.tags.keys():
                    if key == "TXXX:PROMPT":
                        metadata["tags"] = str(audio.tags[key])
                        break
                
                # Extract track ID if available
                for key in audio.tags.keys():
                    if key.startswith("TXXX:TRACKID"):
                        metadata["track_id"] = str(audio.tags[key])
                        break
                
                # Check for cover art
                metadata["has_cover_art"] = any(
                    key.startswith("APIC") for key in audio.tags.keys()
                )
            
            # Add file info
            metadata["duration"] = audio.info.length if audio.info else None
            metadata["bitrate"] = audio.info.bitrate if audio.info else None
            
            return metadata
            
        except Exception as e:
            raise MetadataError(f"Failed to extract metadata from {mp3_path}: {e}")
    
    def validate_mp3(self, mp3_path: str) -> bool:
        """
        Validate if a file is a valid MP3.
        
        Args:
            mp3_path: Path to MP3 file
            
        Returns:
            True if valid MP3, False otherwise
        """
        try:
            MP3(mp3_path)
            return True
        except Exception:
            return False
