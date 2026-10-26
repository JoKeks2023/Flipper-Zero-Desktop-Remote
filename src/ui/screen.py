from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QTransform
from PySide6.QtWidgets import QWidget


def frame_image(data, orientation=0):
    if len(data) != 1024:
        raise ValueError('Expected a 128 × 64 Flipper framebuffer')
    # Flipper/U8G2 stores eight vertical pixels per byte.
    pixels = bytes(0 if data[x + (y // 8) * 128] & (1 << (y % 8)) else 1
                   for y in range(64) for x in range(128))
    image = QImage(pixels, 128, 64, 128, QImage.Format.Format_Indexed8).copy()
    image.setColorTable([QColor('#302b24').rgba(), QColor('#ddc39b').rgba()])
    if orientation:
        image = image.transformed(QTransform().rotate({1: 180, 2: 90, 3: 270}.get(orientation, 0)))
    return image


class ScreenView(QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.stage_color = '#1e1e22'
        self.setMinimumSize(320, 220)
        self.setAccessibleName('Live-Display des Flippers')
        self.setToolTip('Das echte Geräte-Display, live über USB übertragen')

    def set_frame(self, data, orientation=0):
        self.image = frame_image(data, orientation)
        self.update()

    def clear(self):
        self.image = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.stage_color))
        painter.drawRoundedRect(self.rect(), 8, 8)
        area = self.rect().adjusted(16, 16, -16, -16)
        if self.image:
            scale = max(1, min(4, area.width() // self.image.width(), area.height() // self.image.height()))
            image = self.image.scaled(self.image.width() * scale, self.image.height() * scale,
                                      Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            painter.drawImage(area.center().x() - image.width() // 2, area.center().y() - image.height() // 2, image)
        else:
            painter.setPen(QColor('#86868f'))
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter, 'Live-Ansicht ist aus')
