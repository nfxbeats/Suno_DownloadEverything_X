# Library Notes for Suno Downloader

This document explains the libraries used in the Suno Downloader project, their purposes, and which project files use them.

## Production Dependencies

### requests >= 2.31.0
- **Purpose**: HTTP library for making API calls and downloading files
- **Used in**: 
  - `api_client.py` - Makes HTTP requests to Suno API
  - `metadata_handler.py` - Downloads cover art images
  - Used for all network communication with Suno's servers

### colorama >= 0.4.6
- **Purpose**: Cross-platform colored terminal text
- **Used in**:
  - `logger.py` - Provides colored console output for different log levels
  - Makes console output more readable with color-coded messages

### mutagen >= 1.47.0
- **Purpose**: Audio metadata handling library
- **Used in**:
  - `metadata_handler.py` - Embeds metadata into MP3 files (titles, artists, cover art, etc.)
  - Allows embedding of ID3 tags, lyrics, and images into the audio files


## Project Structure Insights

The project follows a modular architecture with:

- **API Communication**: `api_client.py` handles all network requests to Suno
- **Metadata Handling**: `metadata_handler.py` manages audio file tags and embedding
- **Download Management**: `downloader.py` orchestrates the download process
- **Main CLI program**: `main.py` provides the command-line interface for users
- **Support Modules**: `utils.py`, `logger.py`, and `exceptions.py` provide utility functions, logging, and error handling
