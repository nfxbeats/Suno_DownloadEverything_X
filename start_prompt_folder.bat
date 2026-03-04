@echo off
echo ===============================================
echo  Suno Downloader - Interactive Prompt Mode
echo  with Pre-set Download Folder
echo ===============================================
echo.

REM Check if folder parameter was provided
if "%~1"=="" (
    echo Error: Download folder path is required!
    echo Usage: start_prompt_folder.bat "C:\path\to\download\folder"
    echo.
    pause
    exit /b 1
)

REM Store the folder parameter
set "DOWNLOAD_FOLDER=%~1"
echo Download folder set to: %DOWNLOAD_FOLDER%
echo.

REM Check if virtual environment exists
if exist "suno_venv\Scripts\activate.bat" (
    REM Activate virtual environment
    echo Activating virtual environment...
    call suno_venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
) else (
    echo Warning: Virtual environment not found.
    echo Please run setup_windows.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Save the folder as the last used folder so it becomes the default
echo Saving folder as default for prompts...
echo %DOWNLOAD_FOLDER% > last_folder.txt
echo.

REM Run the downloader in prompt mode (will use saved folder as default)
echo Starting Suno Downloader in interactive prompt mode...
echo Note: When prompted for download folder, press Enter to use: %DOWNLOAD_FOLDER%
echo Or enter a different path to override.
echo.
python main.py --prompt --dldata "C:\Users\nfxbe\Downloads\"

REM If the program exits, wait for user to press a key
echo.
echo.
echo Program exited. Press any key to close...
pause >nul
