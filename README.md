# Suno Download Everything X

A simple command-line Python script to bulk download all of your private songs from [Suno AI](https://suno.com/).

This tool iterates through your library pages, downloads each song, and embeds metadata directly into the MP3 files, including track IDs to make your collection more manageable and easier to update.

This is based off the work of [@sunsetacoustic](https://github.com/sunsetsacoustic/Suno_DownloadEverything)


## Features

- **Bulk Download:** Downloads all songs from your private library.
- **Page Range Selection:** Allows downloading songs from a specific range of pages instead of the entire library.
- **Liked-Only Filter:** By default, only downloads songs you've liked. Can be toggled to download all tracks.
- **Track Index Files:** Create a JSON index of tracks instead of downloading them, then use this index later to download specific tracks.
- **Track ID Suffixes:** Appends the last 6 characters of the track ID to filenames (e.g., `My Song_a1b2c3.mp3`) for easy identification and dupe checking. (enabled by default).
- **Skip Existing Files:** Automatically skips downloading tracks that already exist in the download directory, making it easy to resume interrupted downloads or update your collection.
- **Complete Metadata:** Embeds the title, artist, cover art (thumbnail), full track ID, and generation prompt into the MP3 files.
- **File Sanitization:** Cleans up song titles to create valid filenames for any operating system.
- **Duplicate Handling:** If a file with the same name already exists, it saves the new file with a version suffix (e.g., `My Song v2.mp3`) to avoid overwriting.
- **Proxy Support:** Allows routing traffic through an HTTP/S proxy.
- **Multi-Threading:** Downloads multiple tracks simultaneously for faster downloads (default: 4 threads).
- **User-Friendly Output:** Uses colored console output for clear and readable progress updates.
- **Interactive Mode:** Includes a prompt mode that guides you through the setup process.

## Requirements

- [Python 3.12+](https://www.python.org/downloads/)
- `pip` (Python's package installer, usually comes with Python)

## Metadata Features

The downloader embeds several types of metadata into your MP3 files:

1. **Basic Metadata:** Track title and artist name
2. **Thumbnail:** Cover art (if enabled)
3. **Track ID:** The full unique Suno track identifier 
4. **Generation Prompt:** The prompt used to generate the track 
5. **Lyrics:** Any lyrics used

This makes your downloaded tracks more organized and easier to manage in media players that support ID3 tags.

The tags used are as follows:

| MP3 Tag | Description |
| :------ | :---------- |
|TITLE| The title of the track |
|ARTIST| The name of the artist |
|APIC| The embedded cover art image |
|UNSYNCED LYRICS| The lyrics of the song |
|TRACKID| The unique identifier for the track |
|PROMPT| The prompt used to generate the track |

I recommend you use the [Foobar2000 MP3 player](https://www.foobar2000.org/) which is a cross-platform app that allows you to see and copy this data by right clicking on the MP3 and selecting 'Properties'

## Resumable Downloads

One of the key features is the ability to resume interrupted downloads:

1. With the `--with-id-suffix` option enabled (default), each track is saved with a portion of its unique ID in the filename
2. When you run the downloader again, it checks for existing files with matching IDs
3. If a matching file is found, the track is skipped
4. This allows you to safely run the downloader multiple times without duplicating tracks

This is particularly useful for:
- Resuming after network interruptions
- Adding new tracks to your collection
- Fixing partial downloads
- Resuming after your token expires and you copy the new one.


## Windows Easy Installation

1. Download the main zip file from the [main.ZIP file](https://github.com/nfxbeats/Suno_DownloadEverything_X/archive/refs/heads/main.zip)
2. Unzip it into a folder of your choice.
3. Run `setup_windows.bat` to setup the python environment. This only needs to be done once.
4. See the [How to use](#how-to-use) section below.


## Manual Installation

1.  **Clone or download the repository:**
You can download the repository as a ZIP file and extract it. [main.ZIP file](https://github.com/nfxbeats/Suno_DownloadEverything_X/archive/refs/heads/main.zip) 
or
Clone it using git:
    ```bash
    git clone https://github.com/nfxbeats/Suno_DownloadEverything_X.git
    cd your-repo-name
    ```
2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Use

The script requires a **Suno Authorization Token** to access your private library. Here’s how to find it:

### Step 1: Find Your Authorization Token

1.  Open your web browser and go to [suno.com](https://suno.com/) and log in. Go to your Suno library.
2.  Open your browser's **Developer Tools**. You can usually do this by pressing `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac).
3.  Go to the **Network** tab in the Developer Tools.
4.  In the filter box, type `feed` to easily find the right request.
5.  Refresh the Suno page to reload the library. You should see a new request appear in the list.
6.  Click on that request (it might look something like `v2?hide_disliked=...`).
7.  In the new panel that appears, go to the **Headers** tab.
8.  Scroll down to the **Request Headers** section.
9.  Find the `Authorization` header. The value will look like `Bearer [long_string_of_characters]`.
10. **Copy only the long string of characters** (the token itself), *without* the word `Bearer `.

Example (Copy the whole string)
![Example screenshot of the token](images/suno-token.png)


> [!IMPORTANT]
> Your token is like a password. **Do not share it with anyone.** Note that tokens will expire after some time and you will have to follow the steps above to get a fresh token to use.


### Optional: Save Your Token

After copying your token, you can save it to a file named `token.txt` in the same directory as the script. This way, you won't need to manually enter it each time you run the script.

> [!NOTE] 
> Keep this file secure and do not share it with anyone. You should delete it when done as a safety measure.

### Step 2: Run the Script

#### Windows users:
Windows users can simply run `start_prompt.bat` to be prompted for the various options. This will prompt you to enter your token and other settings interactively. Make sure you have run `setup_windows.bat` prior to running `start_prompt.bat`

#### Mac/Linux or manual users:

Open your terminal or command prompt, navigate to the script's directory, and run it using the following command structure.


**Interactive Mode (Recommended):**
```bash
python main.py --prompt
```
This starts an interactive setup process that guides you through all the options.

**Basic Usage (with all default features):**
```bash
python main.py --token-file "token.txt"
```
or 
```bash
python main.py --token "<your pasted token>"
```

**Use Downloads token/workspace files automatically:**
```bash
python main.py --prompt --dldata "C:\\Users\\nfxbe\\Downloads"
```
With `--dldata "<folder>"`, the script will try to load:
- token from `<folder>\\token.txt`
- workspace ID from `<folder>\\wid.txt`

If those files exist and contain valid values, token/workspace prompts are skipped.
When both files exist, the remaining interactive prompts are auto-accepted with defaults.

This will download all your liked songs with thumbnails and track ID suffixes into a folder named `suno-downloads`.

**Custom Directory:**
```bash
python main.py --token-file "token.txt" --directory "My Suno Music"
```
Downloads songs into a custom directory.

**Page Range Usage (download specific page range):**
```bash
python main.py --token-file "token.txt" --start-page 2 --end-page 5
```
This will only download songs from pages 2 through 5 of your library.

**Download All Tracks (not just liked):**
```bash
python main.py --token-file "token.txt" --all-tracks
```
By default, the script only downloads tracks you've liked. This option downloads all your tracks.

**Multi-Threaded Downloads:**
```bash
python main.py --token-file "token.txt" --threads 8
```
This increases the number of concurrent downloads to 8 threads for faster downloading. The default is 4 threads.

**Create an Index File (without downloading):**
```bash
python main.py --token-file "token.txt" --create-index "tracks.json"
```
This creates a JSON file containing information about all tracks matching your criteria (like pages 1-5 or liked-only) without downloading them.

**Download from an Index File:**
```bash
python main.py --token-file "token.txt" --from-index "tracks.json"
```
This downloads only the tracks listed in the specified index file. Useful for downloading a curated list of tracks.

**Resume Interrupted Download:**
Simply run the same command again! The downloader will automatically skip any files that have already been downloaded:
```bash
python main.py --token-file "token.txt" --start-page 1 --end-page 10
```

### Command-Line Arguments

- `--token` **(Required if not using --token-file or --prompt)**: Your Suno authorization token.
- `--token-file` **(Required if not using --token or --prompt)**: Path to a text file containing your Suno authorization token.
- `--prompt` **(Required if not using --token or --token-file)**: Interactive prompt for all download parameters.
- `--dldata <folder>` (Optional): Folder path containing `token.txt` and `wid.txt` (for example `--dldata "C:\Users\nfxbe\Downloads"`). Tip: avoid ending a quoted Windows path with `\` in `cmd.exe`. In prompt mode, token/workspace prompts are skipped when those files are present.
- `--directory` (Optional): The local directory where files will be saved. Defaults to `suno-downloads`.
- `--with-thumbnail` (Optional): Download and embed the song's cover art. **Enabled by default**.
- `--with-id-suffix` (Optional): Append last 6 characters of track ID to filenames. **Enabled by default**.
- `--proxy` (Optional): A proxy server URL (e.g., `http://user:pass@127.0.0.1:8080`). You can provide multiple proxies separated by commas.
- `--threads` (Optional): Number of concurrent download threads. Default is 4. Higher values may download faster but could increase server load.
- `--start-page` (Optional): Starting page number to download from. Defaults to 1 (matches what you see in the Suno UI).
- `--end-page` (Optional): Ending page number to download up to. If not specified, all pages from the start page will be downloaded.
- `--all-tracks` (Optional): Download all tracks, not just the ones you've liked. By default, only liked tracks are downloaded.
- `--create-index` (Optional): Create a JSON index file with the specified filename instead of downloading tracks.
- `--from-index` (Optional): Download tracks from the specified JSON index file.
- `--log-level` (Optional): Set logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Default is `INFO`.
- `--log-file` (Optional): Save logs to a file.


## Disclaimer

This is an unofficial tool and is not affiliated with Suno, Inc. It is intended for personal use only to back up your own creations. Please respect Suno's Terms of Service. The developers of this script are not responsible for any misuse.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
