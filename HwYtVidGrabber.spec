# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Determine icon file based on platform
icon_file = None
if sys.platform == 'win32':
    # For Windows, use .ico format
    icon_file = 'icon.ico'
elif sys.platform == 'darwin':
    # For macOS, use PNG (works well with PyInstaller)
    icon_file = 'icon.png'
else:
    # For Linux, use PNG
    icon_file = 'icon.png'

a = Analysis(
    ['HwYtVidGrabber.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.png', '.'),  # Include PNG icon in the bundle
        ('icon.ico', '.'),  # Include ICO icon in the bundle
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.postprocessor',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HwYtVidGrabber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,  # Use the determined icon file
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='HwYtVidGrabber.app',
        icon=icon_file,
        bundle_identifier='com.malicorporation.hwytvidgrabber',
        info_plist={
            'CFBundleName': 'HwYtVidGrabber',
            'CFBundleDisplayName': 'HwYtVidGrabber',
            'CFBundleIdentifier': 'com.malicorporation.hwytvidgrabber',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2024 MalikHw47. All rights reserved.',
            'NSHighResolutionCapable': True,
            'LSUIElement': False,
        }
    )
