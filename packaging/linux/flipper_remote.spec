# Build on Linux. Keep libraries separate so Qt remains replaceable.
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
