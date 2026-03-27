#!/bin/bash
# ──────────────────────────────────────────────────────────
# DC v2.0 — Build APK using Google Colab
# ──────────────────────────────────────────────────────────
#
# HOW TO USE:
# 1. Open Google Colab: https://colab.research.google.com
# 2. Create a new notebook
# 3. Paste EACH section below into SEPARATE cells and run them in order
#
# ──────────────────────────────────────────────────────────

# ════════════════════════════════════════════════════════════
# CELL 1: Install system dependencies
# ════════════════════════════════════════════════════════════

sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential git ffmpeg libffi-dev libssl-dev \
    python3-venv zip unzip autoconf automake libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    cmake openjdk-17-jdk lld

# Set Java 17
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo "Java: $(java -version 2>&1 | head -1)"

# ════════════════════════════════════════════════════════════
# CELL 2: Install Buildozer and Cython
# ════════════════════════════════════════════════════════════

pip install -q buildozer==1.5.0 cython==0.29.33

echo "Buildozer: $(buildozer --version 2>&1)"
echo "Cython: $(cython --version 2>&1)"

# ════════════════════════════════════════════════════════════
# CELL 3: Clone the repo
# ════════════════════════════════════════════════════════════

cd /content
rm -rf DC
git clone https://github.com/SONUVERMA11/DC.git
cd DC/android_app
echo "Ready to build in: $(pwd)"
ls -la

# ════════════════════════════════════════════════════════════
# CELL 4: Build the APK (takes 10-20 minutes first time)
# ════════════════════════════════════════════════════════════

cd /content/DC/android_app
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

echo "=== Starting build ==="
buildozer -v android debug 2>&1 | tee build.log
echo ""
echo "=== Build exit code: $? ==="

# ════════════════════════════════════════════════════════════
# CELL 5: Download the APK
# ════════════════════════════════════════════════════════════

# Run this cell as Python (not bash):
#
# import glob
# from google.colab import files
#
# apk_files = glob.glob('/content/DC/android_app/bin/*.apk')
# if apk_files:
#     for apk in apk_files:
#         print(f"Downloading: {apk}")
#         files.download(apk)
# else:
#     print("No APK found. Check build.log above for errors.")
#     print("Searching for APK files...")
#     import subprocess
#     result = subprocess.run(['find', '/content/DC', '-name', '*.apk'], capture_output=True, text=True)
#     print(result.stdout or "None found")
