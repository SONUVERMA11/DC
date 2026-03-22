[app]

# App metadata
title = DC
package.name = dc
package.domain = com.dc.musicdl

# Source configuration
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Version
version = 1.0.0

# Python dependencies
# KivyMD 1.2.0 works with Kivy 2.2.1 — removed materialyoucolor/asyncgui/asynckivy/exceptiongroup
# (those are KivyMD 2.x deps that were incorrectly listed)
# websockets removed (no p4a recipe), pillow removed (not essential)
requirements = python3,kivy==2.2.1,kivymd==1.2.0,yt-dlp,requests,certifi,urllib3,charset-normalizer,idna,mutagen,pyjnius

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

# p4a configuration
p4a.branch = develop

# App icon and presplash
icon.filename = %(source.dir)s/icon.png

# Android specific theming
android.presplash_color = #0a0a11

# Log level
[buildozer]
log_level = 2
warn_on_root = 1
