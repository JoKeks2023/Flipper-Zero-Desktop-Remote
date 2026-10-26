"""Render the project's original vector mark at release icon sizes."""
from pathlib import Path
import struct
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

root = Path(__file__).resolve().parents[1]
renderer = QSvgRenderer(str(root / 'src/ui/assets/app-icon.svg'))
icons = root / 'packaging/assets/AppIcon.iconset'
icons.mkdir(parents=True, exist_ok=True)
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        image.save(str(icons / f'icon_{size}x{size}{"@2x" if scale == 2 else ""}.png'))
image.save(str(root / 'packaging/assets/flipper-remote.png'))
chunks = b''
for kind, filename in [('icp4', 'icon_16x16.png'), ('icp5', 'icon_32x32.png'),
                       ('icp6', 'icon_32x32@2x.png'), ('ic07', 'icon_128x128.png'),
                       ('ic08', 'icon_256x256.png'), ('ic09', 'icon_512x512.png'),
                       ('ic10', 'icon_512x512@2x.png')]:
    png = (icons / filename).read_bytes()
    chunks += kind.encode('ascii') + struct.pack('>I', len(png) + 8) + png
(root / 'packaging/assets/AppIcon.icns').write_bytes(b'icns' + struct.pack('>I', len(chunks) + 8) + chunks)
