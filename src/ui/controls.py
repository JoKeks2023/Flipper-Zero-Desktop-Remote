from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QComboBox


class CompactComboBox(QComboBox):
    """Keep a visible selector affordance with the compact cross-platform style."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.palette().text().color(), 1.3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        x, y = self.width() - 14, self.height() / 2
        path = QPainterPath(QPointF(x - 3, y - 1.5))
        path.lineTo(QPointF(x, y + 1.5))
        path.lineTo(QPointF(x + 3, y - 1.5))
        painter.drawPath(path)
