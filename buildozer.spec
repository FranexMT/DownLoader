[app]
# (str) Title of your application
title = DownLoader Pro

# (str) Package name
package.name = downloader

# (str) Package domain (needed for android/ios packaging)
package.domain = org.franex

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,html,js,css,ico,db

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to include all the files)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to include all the files)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license, .git/*

# (str) Application versioning (method 1)
version = 2.1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3, kivy, requests, yt-dlp, plyer, pillow, certifi

# (str) Custom source folders for requirements
# packagestructures = 

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/assets/icon.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid any surprises after an update.
#android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be shown the license when installing SDK
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = main.py

# (list) Android app theme, default is ok for Kivy-based app
# android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Android additional libraries to copy into libs/armeabi
#android.add_libs_armeabi = lib/armeabi/libgnustl_shared.so

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (str) Android additional Java classes to add to the project.
#android.add_javaclasses = lib/bar/foo.java

# (list) Android AAR archives to add
#android.add_aars =

# (list) Android static libraries to add
#android.add_static_libs =

# (list) Android Java libraries to add
#android.add_jars =

# (list) Android dependencies to add
#android.add_dependencies =

# (list) Android compile options
#android.compile_options =

# (list) Android gradle dependencies
#android.gradle_dependencies =

# (list) Android extra-source folders
#android.add_src =

# (list) Android extra res folders
#android.add_res =

# (list) Android build tools to include
#android.add_build_tools =

# (list) Android packaging options
#android.add_packaging_options =

# (list) Android manifest intent filters to add in the activity
#android.manifest.intent_filters =

# (list) Android activity attributes for the main activity
#android.manifest.main_activity_attributes =

# (list) Android activity attributes for each service
#android.manifest.service_attributes =

# (list) Android meta-data to add in the application
#android.manifest.meta_data =

# (list) Android meta-data to add in the main activity
#android.manifest.main_activity_meta_data =

# (list) Android uses-library to add in the manifest
#android.manifest.uses_library =

# (str) Android log level (one of debug, info, warning, error, critical)
android.log_level = debug

# (bool) If True, then the app will be built as a release version
android.release = False

# (str) The path to the keystore for signing the release APK
#android.keystore = /path/to/keystore

# (str) The alias of the key in the keystore
#android.keystore_alias = myalias

# (str) The password for the keystore
#android.keystore_password = mypassword

# (str) The password for the key in the keystore
#android.key_password = mypassword
