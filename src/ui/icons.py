"""A small, consistent set of vector symbols drawn by Qt; no platform clip art."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def icon(name, color='#86868f', active='#e8b080'):
    result = QIcon()
    for state, tint in [(QIcon.State.Off, color), (QIcon.State.On, active)]:
        pixmap = QPixmap(40, 40)
        pixmap.setDevicePixelRatio(2)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(20 / 24, 20 / 24)
        p.setPen(QPen(QColor(tint), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        def line(x1, y1, x2, y2):
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        def path(points):
            shape = QPainterPath(QPointF(*points[0]))
            for point in points[1:]:
                shape.lineTo(QPointF(*point))
            p.drawPath(shape)
        if name == 'home':
            for x, y in [(4, 4), (14, 4), (4, 14), (14, 14)]:
                p.drawRoundedRect(QRectF(x, y, 6, 6), 1, 1)
        elif name in {'remote', 'device'}:
            p.drawRoundedRect(QRectF(3, 5, 18, 13), 2, 2)
            line(9, 21, 15, 21)
            line(12, 18, 12, 21)
            if name == 'device':
                line(6, 9, 11, 9)
                p.drawEllipse(QRectF(15, 10, 2, 2))
        elif name == 'folder':
            path([(3, 8), (3, 5), (10, 5), (12, 8), (21, 8), (21, 20), (3, 20), (3, 8), (21, 8)])
        elif name == 'file':
            path([(5, 3), (14, 3), (19, 8), (19, 21), (5, 21), (5, 3)])
            path([(14, 3), (14, 8), (19, 8)])
            line(8, 12, 16, 12)
            line(8, 16, 14, 16)
        elif name in {'infrared', 'radio'}:
            p.drawEllipse(QRectF(10, 15, 4, 4))
            for rect in [QRectF(7, 10, 10, 10), QRectF(3, 5, 18, 18)]:
                p.drawArc(rect, 35 * 16, 110 * 16)
            if name == 'radio':
                line(12, 19, 12, 22)
        elif name == 'nfc':
            p.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
            line(7, 8, 10, 8)
            for x in [12, 16]:
                p.drawArc(QRectF(x - 3, 8, 6, 9), -65 * 16, 130 * 16)
        elif name == 'usb':
            path([(12, 21), (12, 3), (9, 6), (12, 3), (15, 6)])
            path([(12, 15), (6, 12), (6, 9)])
            path([(12, 12), (18, 9), (18, 7)])
            p.drawEllipse(QRectF(4.5, 6, 3, 3))
            p.drawRect(QRectF(16.5, 4, 3, 3))
        elif name == 'macro':
            path([(7, 4), (19, 12), (7, 20), (7, 4)])
        elif name == 'settings':
            for y, x in [(6, 8), (12, 16), (18, 10)]:
                line(3, y, x - 2, y)
                line(x + 2, y, 21, y)
                p.drawEllipse(QRectF(x - 2, y - 2, 4, 4))
        elif name == 'system':
            p.drawRoundedRect(QRectF(6, 6, 12, 12), 1, 1)
            for n in [8, 12, 16]:
                line(n, 3, n, 6); line(n, 18, n, 21)
                line(3, n, 6, n); line(18, n, 21, n)
        elif name == 'refresh':
            p.drawArc(QRectF(4, 4, 16, 16), 45 * 16, 280 * 16)
            path([(15, 3), (20, 4), (19, 9)])
        elif name == 'up':
            path([(6, 12), (12, 6), (18, 12)])
            line(12, 6, 12, 20)
        elif name == 'chevron':
            path([(9, 6), (15, 12), (9, 18)])
        elif name == 'back':
            path([(10, 6), (4, 12), (10, 18)])
            path([(4, 12), (19, 12), (19, 5)])
        p.end()
        result.addPixmap(pixmap, QIcon.Mode.Normal, state)
    return result


MODULE_ICONS = ['home', 'system', 'remote', 'folder', 'infrared', 'nfc', 'radio', 'usb', 'macro', 'settings']
