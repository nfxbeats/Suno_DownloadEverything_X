@echo off
echo ===============================================
echo  Suno Downloader - Interactive Prompt Mode
echo ===============================================
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

REM Run the downloader in prompt mode
echo Starting Suno Downloader in interactive prompt mode...
echo.
python main.py --prompt

REM If the program exits, wait for user to press a key
echo.
echo.
echo Program exited. Press any key to close...
pause >nul
