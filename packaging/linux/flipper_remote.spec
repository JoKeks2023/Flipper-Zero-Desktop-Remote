# Build on Linux. Qt hooks collect the native platform plugins.
from pathlib import Path
root = Path(SPECPATH).resolve().parents[1]
a = Analysis(
    [str(root / 'src/main.py')], pathex=[str(root / 'src')],
    binaries=[], datas=[(str(root / 'src/ui/legal'), 'ui/legal')], hiddenimports=['serial.tools.list_ports'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='flipper-remote', console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='flipper-remote')
