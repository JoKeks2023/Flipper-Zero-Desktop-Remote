from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtWidgets import QAbstractButton
from ui.icons import icon


class ActionRow(QAbstractButton):
    """One keyboard-accessible, compact destination; whole row is clickable."""
    def __init__(self, title, description, symbol):
        super().__init__()
        self.title, self.description, self.symbol = title, description, symbol
        self.setAccessibleName(title)
        self.setAccessibleDescription(description)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.tokens = None

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def sizeHint(self):
        return QSize(480, 44)

    def paintEvent(self, event):
        if self.tokens is None:
            return
        c = self.tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.underMouse() or self.hasFocus() or self.isDown():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(c['hover'] if not self.isDown() else c['selected']))
            p.drawRoundedRect(self.rect(), 6, 6)
        icon(self.symbol, c['secondary']).paint(p, QRect(12, 12, 20, 20))
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)
        p.setPen(QColor(c['strong']))
        p.drawText(QRect(46, 4, self.width() - 86, 19), Qt.AlignmentFlag.AlignVCenter, self.title)
        font.setWeight(QFont.Weight.Normal)
        font.setPixelSize(12)
        p.setFont(font)
        p.setPen(QColor(c['secondary']))
        text = p.fontMetrics().elidedText(self.description, Qt.TextElideMode.ElideRight, self.width() - 86)
        p.drawText(QRect(46, 23, self.width() - 86, 17), Qt.AlignmentFlag.AlignVCenter, text)
        icon('chevron', c['muted']).paint(p, QRect(self.width() - 30, 13, 16, 16))
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QColor(c['focus']))
            p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
