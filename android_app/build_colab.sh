#!/bin/bash
# ──────────────────────────────────────────────────────────
# Build APK using Google Colab
# ──────────────────────────────────────────────────────────
# 
# HOW TO USE:
# 1. Open Google Colab: https://colab.research.google.com
# 2. Create a new notebook
# 3. Upload your android_app folder to Colab
# 4. Paste and run each section below in separate cells
#
# ──────────────────────────────────────────────────────────

# ── CELL 1: Install Buildozer and dependencies ──
echo "=== Installing build dependencies ==="
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential git ffmpeg libffi-dev libssl-dev \
    python3-venv zip unzip autoconf automake libtool \
    pkg-config zlib1g-dev libncurses5-dev cmake \
    openjdk-17-jdk

pip install -q buildozer cython==0.29.36

# ── CELL 2: Upload and navigate to project ──
# Upload your android_app folder first, then:
# cd /content/android_app

# ── CELL 3: Build the APK ──
echo "=== Building APK (this takes 15-30 minutes on first run) ==="
buildozer -v android debug

# ── CELL 4: Download the APK ──
echo "=== APK built! Downloading... ==="
from google.colab import files
import glob
apk_files = glob.glob('bin/*.apk')
if apk_files:
    files.download(apk_files[0])
    print(f"Downloaded: {apk_files[0]}")
else:
    print("ERROR: No APK found. Check build logs above.")
