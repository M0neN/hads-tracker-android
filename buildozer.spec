[app]
title = HADS Tracker
package.name = hadstracker
package.domain = org.health
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0
requirements = python3,kivy==2.3.1,fpdf
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.3.1
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
p4a.branch = master
android.archs = arm64-v8a
android.allow_backup = True
android.enable_androidx = True
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

[buildozer]
log_level = 2
warn_on_root = 1
