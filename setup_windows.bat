@echo off
echo ===============================================
echo  Suno Downloader - Setup Script for Windows
echo ===============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Check if virtual environment exists
if exist "suno_venv\Scripts\activate.bat" (
    echo Virtual environment already exists.
    echo.
) else (
    echo Creating virtual environment...
    python -m venv suno_venv
    
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please make sure venv module is available.
        pause
        exit /b 1
    )
    
    echo Virtual environment created successfully.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call suno_venv\Scripts\activate.bat
echo Virtual environment activated.
echo.

REM Install required packages
echo Installing required packages...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  Setup completed successfully!
echo  You can now run the Suno Downloader.
echo ===============================================
echo.
echo To use the downloader:
echo 1. Make sure you have a valid token in token.txt
echo 2. Run "python main.py --help" for available options
echo.

pause
