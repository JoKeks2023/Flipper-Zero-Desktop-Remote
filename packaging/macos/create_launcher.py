"""Create a lightweight development .app; requires this checkout and its .venv."""
from pathlib import Path
import plistlib
import shlex

root = Path(__file__).resolve().parents[2]
app = root / 'build' / 'Flipper Zero Desktop Remote.app'
contents = app / 'Contents'
macos = contents / 'MacOS'
macos.mkdir(parents=True, exist_ok=True)
with (contents / 'Info.plist').open('wb') as file:
    plistlib.dump({
        'CFBundleName': 'Flipper Zero Desktop Remote',
        'CFBundleDisplayName': 'Flipper Zero Desktop Remote',
        'CFBundleIdentifier': 'com.jokeks.flipperzerodesktopremote.dev',
        'CFBundleExecutable': 'flipper-remote',
        'CFBundlePackageType': 'APPL',
        'CFBundleVersion': '0.2.0',
        'CFBundleShortVersionString': '0.2.0',
        'LSMinimumSystemVersion': '14.0',
        'NSHighResolutionCapable': True,
    }, file)
launcher = macos / 'flipper-remote'
launcher.write_text('#!/bin/sh\nexec ' + shlex.quote(str(root / '.venv/bin/python')) + ' ' + shlex.quote(str(root / 'src/main.py')) + '\n')
launcher.chmod(0o755)
print(app)
