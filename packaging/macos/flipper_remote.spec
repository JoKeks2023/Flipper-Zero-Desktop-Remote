# Build on macOS. Stdio stays available for the bundled --mcp entry point.
from pathlib import Path
import sys
root = Path(SPECPATH).resolve().parents[1]
sys.path.insert(0, str(root / 'packaging'))
from release_spec import inputs

a = Analysis(
    [str(root / 'src/main.py')], pathex=[str(root / 'src')],
    binaries=[], datas=inputs(root), hiddenimports=['serial.tools.list_ports', 'PySide6.QtSvg'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='flipper-remote', console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='flipper-remote')
app = BUNDLE(coll, name='Flipper Zero Desktop Remote.app',
    icon=str(root / 'packaging/assets/AppIcon.icns'),
    bundle_identifier='com.jokeks.flipperzerodesktopremote',
    info_plist={'CFBundleShortVersionString': '0.2.0', 'CFBundleVersion': '0.2.0',
                'LSMinimumSystemVersion': '14.0', 'NSHighResolutionCapable': True})
