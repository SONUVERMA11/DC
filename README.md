# 🎵 YouTube MP3 Downloader

A modern desktop application to download high-quality music from YouTube in MP3 format with embedded thumbnails and metadata.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

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

## 🚀 Quick Start

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

| Component | Technology |
|-----------|-----------|
| Language | Python 3 |
| Download Engine | yt-dlp |
| Audio Conversion | FFmpeg |
| GUI Framework | CustomTkinter |
| Image Processing | Pillow |
