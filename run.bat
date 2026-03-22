@echo off
echo ============================================
echo   YouTube MP3 Downloader - Setup ^& Launch
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found in PATH.
    echo The app needs FFmpeg for MP3 conversion.
    echo Download from: https://ffmpeg.org/download.html
    echo.
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.

:: Launch app
echo Launching YouTube MP3 Downloader...
python app.py
