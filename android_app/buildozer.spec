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
requirements = python3,kivy==2.3.0,kivymd==1.2.0,yt-dlp,requests,certifi,urllib3,charset-normalizer,idna,pillow,mutagen,websockets,pyjnius

# Orientation and display
orientation = portrait
fullscreen = 0

# Android configuration
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.arch = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

# Gradle options
android.gradle_dependencies = 
android.enable_androidx = True

# p4a configuration
p4a.branch = develop

# App icon and presplash (uncomment and set paths if you have these files)
icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# Android specific theming
android.presplash_color = #0a0a11

# Log level
[buildozer]
log_level = 2
warn_on_root = 1
