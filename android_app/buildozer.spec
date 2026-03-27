[app]

# App metadata
title = DC
package.name = dc
package.domain = com.dc.musicdl

# Source configuration
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Version
version = 2.0.0

# Python dependencies
# KivyMD 1.1.1 is the last stable release compatible with Kivy 2.2.1 + p4a master
# pyjnius is auto-provided by p4a, do NOT list it here
# websockets/pillow removed (no p4a recipe / not essential)
requirements = python3,kivy==2.2.1,kivymd==1.1.1,yt-dlp,requests,certifi,urllib3,charset-normalizer,idna,mutagen

# Orientation and display
orientation = portrait
fullscreen = 0

# Android configuration
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

# Gradle options
android.gradle_dependencies = 
android.enable_androidx = True

# p4a configuration — use master (stable, Python <=3.12)
# DO NOT use develop — it builds hostpython3 with Python 3.14 which breaks Cython
p4a.branch = master

# App icon and presplash
icon.filename = %(source.dir)s/icon.png

# Android specific theming
android.presplash_color = #0D0D14

# Log level
[buildozer]
log_level = 2
warn_on_root = 1
