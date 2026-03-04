"""Command-line interface for Suno Downloader."""

import argparse
import os
import sys
from typing import Optional, Dict, Any

from config import config
from logger import logger, setup_logger
from exceptions import SunoDownloaderError, ConfigurationError, TokenError
from utils import (
    load_token_from_file, save_token_to_file, validate_token,
    load_last_download_folder, save_last_download_folder
)
from downloader import SunoDownloader


DL_TOKEN_FILE = r"C:\Users\nfxbe\Downloads\token.txt"
DL_WORKSPACE_FILE = r"C:\Users\nfxbe\Downloads\wid.txt"


class InteractivePrompt:
    """Interactive prompt for user input."""
    
    @staticmethod
    def prompt_for_input(prompt: str, default: Optional[str] = None) -> str:
        """Prompt user for input with optional default."""
        prompt_str = f"{prompt}"
        if default is not None:
            prompt_str += f" [{default}]"
        prompt_str += ": "
        
        response = input(prompt_str).strip()
        return response if response else (default or "")
    
    @staticmethod
    def prompt_yes_no(prompt: str, default: bool = False) -> bool:
        """Prompt user for yes/no response."""
        default_str = "Y/n" if default else "y/N"
        response = InteractivePrompt.prompt_for_input(f"{prompt} ({default_str})", "").lower()
        
        if not response:
            return default
        
        return response.startswith('y')
    
    def get_token(self) -> str:
        """Get token from user input or file."""
        # Check for existing token file
        if validate_token_file(config.DEFAULT_TOKEN_FILE):
            logger.info(f"Found valid token file: {config.DEFAULT_TOKEN_FILE}")
            if self.prompt_yes_no("Use existing token file?", True):
                return load_token_from_file(config.DEFAULT_TOKEN_FILE)
        
        # Prompt for token file path
        token_file = "" #self.prompt_for_input(            "Enter path to token file (or leave empty to paste token directly)"        )
        
        if token_file:
            try:
                return load_token_from_file(token_file)
            except ConfigurationError:
                logger.warning(f"Could not load token from {token_file}")
        
        # Get token directly from user
        token = self.prompt_for_input("Please paste your Suno token")
        
        if not validate_token(token):
            raise TokenError("Invalid token format")
        
        # Ask to save token
        if self.prompt_yes_no("Save this token for later use?"):
            save_path = self.prompt_for_input("Enter file path to save token", config.DEFAULT_TOKEN_FILE)
            try:
                save_token_to_file(token, save_path)
                logger.info(f"Token saved to {save_path}")
            except ConfigurationError as e:
                logger.warning(f"Could not save token: {e}")
        
        return token
    
    def get_download_options(self, preset_workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get download options from user."""
        options = {}
        
        # Get last used download folder or fallback to default
        last_folder = load_last_download_folder() or config.DEFAULT_DOWNLOAD_DIR
        
        # Check for workspace ID first
        workspace_id = preset_workspace_id
        if workspace_id is None:
            workspace_id = self.prompt_for_input(
                "Enter workspace ID to download (leave empty to download from feed)",
                ""
            )
        
        if workspace_id:
            # If workspace ID provided, set minimal options and return
            options['workspace_id'] = workspace_id
            options['directory'] = self.prompt_for_input(
                "Enter download folder path", 
                last_folder
            )
            
            # Thread count for concurrent downloads
            thread_count = self.prompt_for_input(
                "Number of download threads", 
                str(config.DEFAULT_THREADS)
            )
            try:
                options['threads'] = int(thread_count)
            except ValueError:
                options['threads'] = config.DEFAULT_THREADS
                logger.warning(f"Invalid thread count, using default: {config.DEFAULT_THREADS}")
            
            # Thumbnails
            options['with_thumbnails'] = self.prompt_yes_no("Download and embed thumbnails?", True)
            
            # ID suffix
            options['with_id_suffix'] = self.prompt_yes_no("Add track ID suffix to filenames?", True)
            
            # Proxy
            proxy = self.prompt_for_input("Enter proxy string (leave empty for none)", "")
            if proxy:
                options['proxy'] = proxy
            
            return options
        
        # Continue with regular feed download options
        # Download directory
        options['directory'] = self.prompt_for_input(
            "Enter download folder path", 
            last_folder
        )
        
        # Thread count for concurrent downloads
        thread_count = self.prompt_for_input(
            "Number of download threads", 
            str(config.DEFAULT_THREADS)
        )
        try:
            options['threads'] = int(thread_count)
        except ValueError:
            options['threads'] = config.DEFAULT_THREADS
            logger.warning(f"Invalid thread count, using default: {config.DEFAULT_THREADS}")
        
        # Thumbnails
        options['with_thumbnails'] = self.prompt_yes_no("Download and embed thumbnails?", True)
        
        # ID suffix
        options['with_id_suffix'] = self.prompt_yes_no("Add track ID suffix to filenames?", True)
        
        # Track selection
        options['liked_only'] = self.prompt_yes_no("Download only liked tracks?", True)
        
        # Page range
        options['start_page'] = int(self.prompt_for_input("Start page", "1"))
        end_page_input = self.prompt_for_input("End page (leave empty for all pages)", "")
        if end_page_input:
            options['end_page'] = int(end_page_input)
        
        # Proxy
        proxy = self.prompt_for_input("Enter proxy string (leave empty for none)", "")
        if proxy:
            options['proxy'] = proxy
        
        return options


def validate_token_file(filepath: str) -> bool:
    """Check if token file exists and contains valid token."""
    try:
        token = load_token_from_file(filepath)
        return validate_token(token)
    except:
        return False


def load_workspace_id_from_file(filepath: str) -> str:
    """Load workspace ID from a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            workspace_id = f.read().strip()

        if not workspace_id:
            raise ConfigurationError(f"Workspace ID file is empty: {filepath}")

        logger.info(f"Workspace ID loaded from {filepath}")
        return workspace_id
    except FileNotFoundError:
        raise ConfigurationError(f"Workspace ID file not found: {filepath}")
    except Exception as e:
        raise ConfigurationError(f"Error reading workspace ID file {filepath}: {e}")


def load_dldata_values() -> Dict[str, Optional[str]]:
    """Load token/workspace from fixed Downloads files for --dldata mode."""
    values: Dict[str, Optional[str]] = {"token": None, "workspace_id": None}

    if os.path.isfile(DL_TOKEN_FILE):
        try:
            values["token"] = load_token_from_file(DL_TOKEN_FILE)
        except ConfigurationError as e:
            logger.warning(f"Could not load --dldata token file: {e}")

    if os.path.isfile(DL_WORKSPACE_FILE):
        try:
            values["workspace_id"] = load_workspace_id_from_file(DL_WORKSPACE_FILE)
        except ConfigurationError as e:
            logger.warning(f"Could not load --dldata workspace file: {e}")

    return values


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Bulk download your private Suno songs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --token "your_token_here"
  %(prog)s --token-file token.txt --with-thumbnail
  %(prog)s --prompt
  %(prog)s --test-api
        """
    )
    
    # Token options (mutually exclusive)
    token_group = parser.add_mutually_exclusive_group()
    token_group.add_argument(
        "--token", 
        type=str, 
        help="Your Suno session Bearer Token"
    )
    token_group.add_argument(
        "--token-file", 
        type=str, 
        help="Path to file containing your Suno session Bearer Token"
    )
    token_group.add_argument(
        "--prompt", 
        action="store_true", 
        help="Interactive prompt for all download parameters"
    )
    token_group.add_argument(
        "--test-api", 
        action="store_true", 
        help="Test API connection and display available data"
    )
    token_group.add_argument(
        "--test-playlist", 
        action="store_true", 
        help="Test playlist API connection"
    )
    
    # Workspace options
    parser.add_argument(
        "--dldata",
        action="store_true",
        help=(
            "Load token from C:\\Users\\nfxbe\\Downloads\\token.txt and workspace ID "
            "from C:\\Users\\nfxbe\\Downloads\\wid.txt when available"
        )
    )
    parser.add_argument(
        "--list-workspaces", 
        action="store_true", 
        help="List all workspaces (projects) to workspaces.json"
    )
    parser.add_argument(
        "--download-workspace", 
        type=str,
        metavar="WORKSPACE_ID",
        help="Download all tracks from a specific workspace by ID"
    )
    
    # Download options
    parser.add_argument(
        "--directory", 
        type=str, 
        default=config.DEFAULT_DOWNLOAD_DIR,
        help=f"Local directory for saving files (default: {config.DEFAULT_DOWNLOAD_DIR})"
    )
    parser.add_argument(
        "--with-thumbnail", 
        action="store_true", 
        help="Embed the song's thumbnail"
    )
    parser.add_argument(
        "--with-id-suffix", 
        action="store_true", 
        help="Append last 6 characters of track ID to filename"
    )
    parser.add_argument(
        "--proxy", 
        type=str, 
        help="Proxy with protocol (comma-separated)"
    )
    
    # Thread options
    parser.add_argument(
        "--threads", 
        type=int, 
        default=config.DEFAULT_THREADS, 
        help=f"Number of concurrent download threads (default: {config.DEFAULT_THREADS})"
    )
    
    # Page range options
    parser.add_argument(
        "--start-page", 
        type=int, 
        default=1, 
        help="Starting page number as shown in Suno UI (default: 1)"
    )
    parser.add_argument(
        "--end-page", 
        type=int, 
        help="Ending page number as shown in Suno UI (default: download all pages)"
    )
    parser.add_argument(
        "--all-tracks", 
        action="store_true", 
        help="Download all tracks, not just liked tracks"
    )
    
    # Index file options
    parser.add_argument(
        "--create-index", 
        type=str, 
        help="Create a JSON index file instead of downloading"
    )
    parser.add_argument(
        "--from-index", 
        type=str, 
        help="Download tracks from specified JSON index file"
    )
    parser.add_argument(
        "--workspace-index", 
        type=str, 
        default=config.DEFAULT_WORKSPACE_INDEX,
        help=f"Filename for workspace index (default: {config.DEFAULT_WORKSPACE_INDEX})"
    )
    
    # Playlist options
    parser.add_argument(
        "--playlist-index", 
        type=str, 
        default=config.DEFAULT_PLAYLIST_INDEX,
        help=f"Filename for playlist index (default: {config.DEFAULT_PLAYLIST_INDEX})"
    )
    parser.add_argument(
        "--skip-playlist-index", 
        action="store_true", 
        help="Skip saving playlist index"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level", 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
        default='INFO',
        help="Set logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        help="Save logs to file"
    )
    
    return parser


def handle_interactive_mode(use_dldata: bool = False) -> Dict[str, Any]:
    """Handle interactive mode and return configuration."""
    prompt = InteractivePrompt()
    
    logger.info("=== Suno Downloader - Interactive Setup ===")
    
    dldata_values = load_dldata_values() if use_dldata else {"token": None, "workspace_id": None}

    # Get token
    token = dldata_values.get("token")
    if token:
        logger.info("Using token from --dldata file")
    else:
        token = prompt.get_token()
    
    # Get download options
    preset_workspace_id = dldata_values.get("workspace_id")
    if preset_workspace_id:
        logger.info("Using workspace ID from --dldata file")

    options = prompt.get_download_options(preset_workspace_id=preset_workspace_id)
    options['token'] = token
    
    return options


def handle_test_mode(args: argparse.Namespace) -> None:
    """Handle test mode operations."""
    # Get token for testing
    dldata_values = load_dldata_values() if args.dldata else {"token": None}

    if args.token:
        token = args.token
    elif args.token_file:
        token = load_token_from_file(args.token_file)
    elif dldata_values.get("token"):
        token = dldata_values["token"]
    elif validate_token_file(config.DEFAULT_TOKEN_FILE):
        token = load_token_from_file(config.DEFAULT_TOKEN_FILE)
    else:
        prompt = InteractivePrompt()
        token = prompt.get_token()
    
    # Parse proxy list
    proxies_list = args.proxy.split(",") if args.proxy else None
    
    # Create downloader for testing
    downloader = SunoDownloader(token, proxies_list=proxies_list)
    
    try:
        if args.test_api:
            # Test API connection
            prompt = InteractivePrompt()
            page = int(prompt.prompt_for_input("Enter page number to test", "1"))
            liked_only = prompt.prompt_yes_no("Only show liked tracks?", True)
            
            data = downloader.test_connection(page, liked_only)
            logger.info("API test successful!")
            
            # Show sample data
            clips = data if isinstance(data, list) else data.get("clips", [])
            if clips:
                logger.info(f"Found {len(clips)} clips on page {page}")
                sample_clip = clips[0]
                logger.info(f"Sample track: {sample_clip.get('title', 'Unknown')}")
        
        elif args.test_playlist:
            # Test playlist API
            data = downloader.api_client.get_playlist_page(1)
            logger.info("Playlist API test successful!")
            
            playlists = data.get("playlists", [])
            if playlists:
                logger.info(f"Found {len(playlists)} playlists")
                for i, playlist in enumerate(playlists[:3]):
                    logger.info(f"Playlist {i+1}: {playlist.get('name', 'Unknown')}")
        
        elif args.list_workspaces:
            # List workspaces to JSON file
            stats = downloader.create_workspaces_index(args.workspace_index)
            logger.info(f"Workspaces index created: {stats['workspaces_indexed']} workspaces")
            logger.info(f"Saved to: {stats['index_file']}")
    
    finally:
        downloader.close()


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logger(level=args.log_level, log_file=args.log_file)
    
    try:
        # Handle different modes
        if args.prompt:
            # Interactive mode
            config_dict = handle_interactive_mode(use_dldata=args.dldata)
            
        elif args.test_api or args.test_playlist or args.list_workspaces:
            # Test mode or workspace listing
            handle_test_mode(args)
            return
        
        elif args.download_workspace:
            # Download workspace mode
            dldata_values = load_dldata_values() if args.dldata else {"token": None}

            if not (args.token or args.token_file or dldata_values.get("token")):
                if not validate_token_file(config.DEFAULT_TOKEN_FILE):
                    parser.error("Token required for workspace download")
            
            # Get token
            if args.token:
                token = args.token
            elif args.token_file:
                token = load_token_from_file(args.token_file)
            elif dldata_values.get("token"):
                token = dldata_values["token"]
            else:
                token = load_token_from_file(config.DEFAULT_TOKEN_FILE)
            
            # Validate token
            if not validate_token(token):
                raise TokenError("Invalid token format")
            
            # Parse proxy list
            proxies_list = args.proxy.split(",") if args.proxy else None
            
            # Create downloader
            downloader = SunoDownloader(
                token=token,
                download_dir=args.directory,
                proxies_list=proxies_list,
                with_thumbnails=args.with_thumbnail,
                with_id_suffix=args.with_id_suffix,
                max_threads=args.threads
            )
            
            try:
                stats = downloader.download_workspace(args.download_workspace)
                logger.info(f"Workspace download complete: {stats['downloaded']}/{stats['total_tracks']} tracks")
                # Save the folder path for future use
                save_last_download_folder(args.directory)
            finally:
                downloader.close()
            return
            
        else:
            # Command-line mode
            dldata_values = load_dldata_values() if args.dldata else {"token": None}

            if not (args.token or args.token_file or dldata_values.get("token")):
                parser.error("Either --token, --token-file, or --prompt is required")
            
            # Get token
            if args.token:
                token = args.token
            elif args.token_file:
                token = load_token_from_file(args.token_file)
            elif dldata_values.get("token"):
                token = dldata_values["token"]
            else:
                token = load_token_from_file(config.DEFAULT_TOKEN_FILE)
            
            # Validate token
            if not validate_token(token):
                raise TokenError("Invalid token format")
            
            config_dict = {
                'token': token,
                'directory': args.directory,
                'with_thumbnails': args.with_thumbnail,
                'with_id_suffix': args.with_id_suffix,
                'start_page': args.start_page,
                'end_page': args.end_page,
                'liked_only': not args.all_tracks,
                'proxy': args.proxy,
                'threads': args.threads,
                'create_index': args.create_index,
                'from_index': args.from_index
            }
        
        # Parse proxy list
        proxies_list = None
        if config_dict.get('proxy'):
            proxies_list = config_dict['proxy'].split(",")
        
        # Create downloader
        downloader = SunoDownloader(
            token=config_dict['token'],
            download_dir=config_dict['directory'],
            proxies_list=proxies_list,
            with_thumbnails=config_dict.get('with_thumbnails', True),
            with_id_suffix=config_dict.get('with_id_suffix', True),
            max_threads=config_dict.get('threads', config.DEFAULT_THREADS)
        )
        
        try:
            # Execute download operation
            if config_dict.get('workspace_id'):
                # Download workspace
                stats = downloader.download_workspace(config_dict['workspace_id'])
                logger.info(f"Workspace download complete: {stats['downloaded']}/{stats['total_tracks']} tracks")
                # Save the folder path for future use
                save_last_download_folder(config_dict['directory'])
                
            elif config_dict.get('create_index'):
                # Create index file
                stats = downloader.create_index(
                    config_dict['create_index'],
                    config_dict.get('start_page', 1),
                    config_dict.get('end_page'),
                    config_dict.get('liked_only', True)
                )
                logger.info(f"Index created: {stats['tracks_indexed']} tracks")
                
            elif config_dict.get('from_index'):
                # Download from index
                stats = downloader.download_from_index(config_dict['from_index'])
                logger.info(f"Download complete: {stats['downloaded']} tracks")
                # Save the folder path for future use
                save_last_download_folder(config_dict['directory'])
                
            else:
                # Download from API
                stats = downloader.download_from_api(
                    config_dict.get('start_page', 1),
                    config_dict.get('end_page'),
                    config_dict.get('liked_only', True)
                )
                logger.info(f"Download complete: {stats['downloaded']} tracks")
                # Save the folder path for future use
                save_last_download_folder(config_dict['directory'])
        
        finally:
            downloader.close()
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except SunoDownloaderError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
