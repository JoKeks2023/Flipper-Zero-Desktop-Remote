"""Compact desktop theme. Widget roles share these semantic surface tokens."""
from PySide6.QtGui import QColor, QPalette


def colors(dark):
    if dark:
        return dict(bg='#121214', side='#19191c', surface='#1e1e22', hover='#29292d',
                    input='#242428', border='#34343a', text='#d1d1d6', strong='#f3f3f5',
                    secondary='#a6a6ae', muted='#86868f', selected='#33271e',
                    accent='#e8b080', solid='#a44e13', focus='#c78047')
    return dict(bg='#ffffff', side='#f5f5f6', surface='#f2f2f3', hover='#e9e9eb',
                input='#f2f2f3', border='#d3d3d7', text='#3a3a3f', strong='#17171a',
                secondary='#5c5c63', muted='#78787f', selected='#f6eade',
                accent='#914611', solid='#a44e13', focus='#b56a2d')


def palette(tokens):
    p = QPalette()
    for role, key in [('Window', 'bg'), ('WindowText', 'text'), ('Base', 'bg'),
                      ('AlternateBase', 'surface'), ('Text', 'text'), ('Button', 'surface'),
                      ('ButtonText', 'text'), ('Highlight', 'selected'),
                      ('HighlightedText', 'strong'), ('ToolTipBase', 'surface'), ('ToolTipText', 'text')]:
        p.setColor(getattr(QPalette.ColorRole, role), QColor(tokens[key]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(tokens['muted']))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(tokens['muted']))
    return p


def stylesheet(c):
    return f'''
        QWidget {{ color: {c['text']}; font-size: 13px; }}
        QMainWindow, QWidget#workspace {{ background: {c['bg']}; }}
        QFrame#sidebarShell {{ background: {c['side']}; }}
        QFrame#toolbar {{ background: {c['bg']}; border-bottom: 1px solid {c['border']}; }}
        QLabel {{ background: transparent; }}
        QLabel#brand {{ color: {c['strong']}; font-size: 15px; font-weight: 600; }}
        QLabel#brandCaption, QLabel#caption, QLabel#sectionLabel {{ color: {c['muted']}; font-size: 11px; }}
        QLabel#pageTitle {{ color: {c['strong']}; font-size: 19px; font-weight: 600; }}
        QLabel#subtitle {{ color: {c['secondary']}; font-size: 12px; }}
        QLabel#cardTitle {{ color: {c['strong']}; font-size: 13px; font-weight: 500; }}
        QLabel#deviceName {{ color: {c['strong']}; font-size: 13px; font-weight: 500; }}
        QLabel#connectionDot {{ font-size: 8px; }}
        QLabel#connectionStatus {{ color: {c['secondary']}; font-size: 12px; }}
        QFrame#deviceSummary {{ background: {c['surface']}; border: none; border-radius: 8px; }}
        QScrollArea, QScrollArea > QWidget > QWidget {{ background: {c['bg']}; }}
        QFrame#dashboardMetrics {{ background: {c['surface']}; border-radius: 8px; }}
        QFrame#dashboardDivider {{ background: {c['border']}; }}
        QLabel#deviceHeading {{ color: {c['strong']}; font-size: 15px; font-weight: 600; }}
        QLabel#metricLabel {{ color: {c['secondary']}; font-size: 12px; }}
        QLabel#metricValue {{ color: {c['strong']}; font-size: 28px; font-weight: 500; }}
        QLabel#metricNote {{ color: {c['secondary']}; font-size: 11px; }}
        QLabel#detailValue {{ color: {c['strong']}; font-size: 12px; }}
        QProgressBar#batteryLevel {{ background: {c['border']}; border: none; border-radius: 2px; }}
        QProgressBar#batteryLevel::chunk {{ background: {c['accent']}; border-radius: 2px; }}
        QDialog {{ background: {c['bg']}; }}
        QTabWidget::pane {{ border: 1px solid {c['border']}; }}
        QTabBar::tab {{ background: {c['surface']}; color: {c['secondary']}; padding: 7px 12px; }}
        QTabBar::tab:selected {{ background: {c['selected']}; color: {c['accent']}; }}
        QWidget#sidebar {{ background: transparent; }}
        QWidget#sidebar QPushButton {{ background: transparent; text-align: left; border: none; padding: 7px 10px; border-radius: 6px; font-size: 12px; font-weight: 400; }}
        QWidget#sidebar QPushButton:hover {{ background: {c['hover']}; }}
        QWidget#sidebar QPushButton:checked {{ background: {c['selected']}; color: {c['accent']}; font-weight: 500; }}
        QPushButton {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 5px 10px; min-height: 18px; font-size: 12px; font-weight: 500; }}
        QPushButton:hover {{ background: {c['hover']}; }}
        QPushButton:pressed {{ background: {c['input']}; }}
        QPushButton:focus {{ border: 1px solid {c['focus']}; }}
        QPushButton:disabled {{ color: {c['muted']}; border-color: transparent; background: {c['surface']}; }}
        QPushButton[role="primary"] {{ background: {c['solid']}; border-color: {c['solid']}; color: #ffffff; }}
        QPushButton[role="primary"]:hover {{ background: #914611; }}
        QPushButton[role="primary"]:pressed {{ background: #7d3c0f; }}
        QPushButton[role="primary"]:disabled {{ background: {c['surface']}; color: {c['muted']}; border-color: transparent; }}
        QPushButton[role="ghost"] {{ background: transparent; border-color: transparent; color: {c['secondary']}; }}
        QPushButton[role="ghost"]:hover {{ background: {c['hover']}; color: {c['strong']}; }}
        QPushButton[role="danger"] {{ background: transparent; border-color: transparent; color: {c['secondary']}; }}
        QPushButton[role="danger"]:hover {{ background: {c['hover']}; color: #d64c54; }}
        QPushButton#remoteKey {{ background: {c['surface']}; border: 1px solid {c['border']}; padding: 0; font-size: 17px; min-height: 0; }}
        QPushButton#remoteKey:hover {{ background: {c['hover']}; border-color: {c['muted']}; }}
        QPushButton#remoteKey:pressed {{ background: {c['selected']}; color: {c['accent']}; border-color: {c['focus']}; }}
        QPushButton#remoteKey[center="true"] {{ color: {c['accent']}; background: {c['selected']}; font-size: 12px; font-weight: 600; }}
        QPushButton#remoteBack {{ background: transparent; border-color: transparent; color: {c['secondary']}; }}
        QPushButton#remoteBack:hover {{ background: {c['hover']}; }}
        QComboBox, QLineEdit {{ background: {c['input']}; border: 1px solid transparent; border-radius: 6px; padding: 5px 24px 5px 8px; font-size: 12px; min-height: 18px; selection-background-color: {c['selected']}; }}
        QComboBox:focus, QLineEdit:focus {{ border-color: {c['focus']}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
        QComboBox QAbstractItemView {{ background: {c['surface']}; color: {c['text']}; selection-background-color: {c['selected']}; border: 1px solid {c['border']}; padding: 4px; }}
        QPlainTextEdit {{ background: {c['surface']}; border: none; border-radius: 6px; padding: 8px; font-size: 12px; selection-background-color: {c['selected']}; }}
        QTreeWidget {{ background: {c['bg']}; alternate-background-color: {c['surface']}; border: none; outline: none; font-size: 12px; }}
        QTreeWidget::item {{ padding: 3px 6px; min-height: 16px; border: none; }}
        QTreeWidget::item:selected {{ background: {c['selected']}; color: {c['strong']}; }}
        QHeaderView::section {{ background: {c['bg']}; color: {c['muted']}; border: none; border-bottom: 1px solid {c['border']}; padding: 7px 6px; font-size: 11px; font-weight: 500; }}
        QGroupBox {{ border: none; padding-top: 18px; margin-top: 0; font-size: 11px; color: {c['muted']}; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0; }}
        QCheckBox {{ spacing: 6px; font-size: 12px; }}
        QCheckBox::indicator {{ width: 14px; height: 14px; }}
        QStatusBar {{ background: {c['bg']}; color: {c['muted']}; border-top: 1px solid {c['border']}; font-size: 11px; }}
        QStatusBar::item {{ border: none; }}
        QDockWidget {{ font-size: 11px; color: {c['muted']}; }}
        QSplitter::handle {{ background: {c['border']}; width: 1px; height: 1px; }}
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 4px; min-height: 24px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QToolTip {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']}; padding: 5px; }}
    '''
