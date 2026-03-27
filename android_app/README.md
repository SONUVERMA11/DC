# DC — YouTube MP3 Downloader (Android)

A premium Material Design 3 YouTube MP3 downloader for Android, built with **KivyMD**.

## ✨ What's New in v2.0

- 🎨 **Modernized UI** — gradient header, glassmorphism cards, animated progress, premium dark/light themes
- 🔥 **Firebase App Distribution** — auto-upload APK for easy sharing
- 🖼️ **New App Icon** — fresh, modern design with purple-cyan gradient
- 📊 **Status chips** — color-coded download status with icons
- 🎯 **Floating download button** — prominent action button

## Features

- 🎵 Download YouTube audio as high-quality MP3 (up to 320kbps)
- 📋 Playlist support — paste any playlist URL
- 🌙 Premium AMOLED dark & warm light theme toggle
- 📊 Real-time progress with speed & ETA
- 🎨 Material Design 3 UI with custom design system
- ❌ Cancel and clear downloads
- 📁 Saves to `Music/YT Downloads/`

## Project Structure

```
android_app/
├── main.py              # KivyMD app (UI + logic)
├── downloader.py        # Download engine (yt-dlp)
├── icon.png             # App icon (512x512)
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

### Option 2: Firebase App Distribution

APKs are automatically uploaded to Firebase App Distribution when GitHub secrets are configured:

1. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Add an Android app with package name `com.dc.musicdl`
3. Create a Google Cloud Service Account with "Firebase App Distribution Admin" role
4. Add these GitHub secrets:
   - `FIREBASE_APP_ID` — your Firebase App ID
   - `FIREBASE_SERVICE_ACCOUNT_JSON` — JSON key content
5. Push to `main` branch — APK auto-uploads to Firebase

### Option 3: Google Colab (Free)

1. Open [Google Colab](https://colab.research.google.com)
2. Upload the `android_app/` folder
3. Run the commands from `build_colab.sh` in cells
4. Download the generated APK

### Option 4: WSL (Windows Subsystem for Linux)

```bash
# In WSL Ubuntu:
sudo apt install build-essential git ffmpeg openjdk-17-jdk
pip install buildozer cython==0.29.33
cd /mnt/f/Ongoing\ Projects/mp3\ yt\ dwonloader/android_app
buildozer -v android debug
```

The APK will be in `android_app/bin/`.

## Requirements

The app bundles these Python packages:
- `kivy` 2.2.1
- `kivymd` 1.1.1
- `yt-dlp` (latest)
- `requests`, `mutagen`

## Notes

- **FFmpeg**: If ffmpeg is not available on the device, the app downloads audio in M4A format instead of MP3. Both are high quality.
- **Storage**: Downloads are saved to `/storage/emulated/0/Music/YT Downloads/`
- **First build** takes 10-20 minutes as it downloads and compiles all dependencies.
