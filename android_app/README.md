# YT MP3 Downloader — Android App

A modern Material Design YouTube MP3 downloader for Android, built with **KivyMD**.

## Features

- 🎵 Download YouTube audio as high-quality MP3 (up to 320kbps)
- 📋 Playlist support — paste any playlist URL
- 🌙 Pure dark (AMOLED) and light theme toggle
- 📊 Real-time progress with speed & ETA
- 🎨 Modern Material Design 3 UI
- ❌ Cancel and clear downloads
- 📁 Saves to `Music/YT Downloads/`

## Project Structure

```
android_app/
├── main.py              # KivyMD app (UI + logic)
├── downloader.py        # Download engine (yt-dlp)
├── buildozer.spec       # Android build config
├── build_colab.sh       # Google Colab build helper
└── README.md            # This file
```

## How to Build the APK

> **Note:** Buildozer only runs on **Linux** or **macOS**. On Windows, use one of the options below.

### Option 1: GitHub Actions (Recommended)

1. Push this repo to GitHub
2. The `.github/workflows/build_apk.yml` workflow triggers automatically
3. Go to **Actions** tab → download the APK artifact
4. Install on your Android device

### Option 2: Google Colab (Free)

1. Open [Google Colab](https://colab.research.google.com)
2. Upload the `android_app/` folder
3. Run the commands from `build_colab.sh` in cells
4. Download the generated APK

### Option 3: WSL (Windows Subsystem for Linux)

```bash
# In WSL Ubuntu:
sudo apt install build-essential git ffmpeg openjdk-17-jdk
pip install buildozer cython==0.29.36
cd /mnt/f/Ongoing\ Projects/mp3\ yt\ dwonloader/android_app
buildozer -v android debug
```

The APK will be in `android_app/bin/`.

## Requirements

The app bundles these Python packages:
- `kivy` 2.3.0
- `kivymd` 1.2.0
- `yt-dlp` (latest)
- `requests`, `pillow`, `mutagen`

## Notes

- **FFmpeg**: If ffmpeg is not available on the device, the app downloads audio in M4A format instead of MP3. Both are high quality.
- **Storage**: Downloads are saved to `/storage/emulated/0/Music/YT Downloads/`
- **First build** takes 15-30 minutes as it downloads and compiles all dependencies. Subsequent builds are much faster.
