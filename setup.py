"""
Setup script for py2app to create a standalone macOS application.
"""
from setuptools import setup

APP = ['gui_app.py']
DATA_FILES = []
ICON = 'thumbnail.icns'

OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON,  # App icon (.icns format)
    'plist': {
        'CFBundleName': 'Posture Corrector',
        'CFBundleDisplayName': 'Posture Corrector',
        'CFBundleGetInfoString': 'Posture monitoring application',
        'CFBundleIdentifier': 'com.posturecorrector.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024',
        'LSUIElement': False,  # Show in dock (windowed app)
        'NSHighResolutionCapable': True,
        'CFBundleIconFile': 'thumbnail',  # Icon file (without .icns extension)
        'NSCameraUsageDescription': 'Posture Corrector needs camera access to monitor your posture using pose detection.',
        'NSMicrophoneUsageDescription': 'Not used, but required for some camera APIs.',
    },
    'packages': [
        'PySide6',
        'cv2',
        'mediapipe',
        'numpy',
    ],
    'includes': [
        'posture_monitor',
        'warning_popup',
        'camera_preview',
        'cv2',
        'numpy',
        'mediapipe',
    ],
    'excludes': [
        'tkinter',
        'matplotlib',
        'pandas',
    ],
}

setup(
    name='Posture Corrector',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

