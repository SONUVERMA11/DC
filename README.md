# 🎵 DC — YouTube MP3 Downloader

A modern application to download high-quality music from YouTube in MP3 format with embedded thumbnails and metadata. Available for **Desktop** and **Android**.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Android](https://img.shields.io/badge/Android-APK-brightgreen?logo=android)

## 📱 Android App (v2.0)

The Android app features a **premium Material Design 3** interface with:
- Gradient header & glassmorphism cards
- AMOLED dark & light theme toggle
- Status chips with color-coded download states
- Firebase App Distribution for easy APK sharing

📥 **Get the APK:** [GitHub Actions](https://github.com/SONUVERMA11/DC/actions) → download latest artifact

See [`android_app/README.md`](android_app/README.md) for build instructions.

## ✨ Features

- **High-Quality MP3** — Download audio at up to 320kbps
- **Embedded Thumbnails** — Album art embedded directly in the MP3 file
- **Full Metadata** — Title, artist, album, and more preserved in ID3 tags
- **Playlist Support** — Paste a playlist URL to download all tracks
- **Batch Downloads** — Add multiple URLs and download them all at once
- **Concurrent Downloads** — Up to 3 simultaneous downloads
- **Modern Dark UI** — Beautiful dark-themed interface
- **Progress Tracking** — Real-time progress bars, speed, and ETA
- **Cancel Support** — Cancel individual downloads anytime

## 📋 Prerequisites

1. **Python 3.9+** — [Download](https://python.org)
2. **FFmpeg** — Required for MP3 conversion and thumbnail embedding
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - Or install via: `winget install FFmpeg` / `choco install ffmpeg`

## 🚀 Quick Start (Desktop)

### Option 1: Double-click launcher
```
run.bat
```

### Option 2: Manual setup
```bash
pip install -r requirements.txt
python app.py
```

## 📖 Usage

1. **Paste URL** — Enter a YouTube video or playlist URL
2. **Click Add** — The app will resolve the URL and add tracks to the queue
3. **Choose Quality** — Select bitrate (128–320kbps)
4. **Choose Output Folder** — Default: `~/Music/YouTube Downloads`
5. **Click Download All** — All queued tracks will download concurrently

## 🛠 Tech Stack

| Component | Desktop | Android |
|-----------|---------|---------|
| Language | Python 3 | Python 3 |
| Download Engine | yt-dlp | yt-dlp |
| Audio Conversion | FFmpeg | FFmpeg (optional) |
| GUI Framework | CustomTkinter | KivyMD 1.1.1 |
| Distribution | — | Firebase App Distribution |
