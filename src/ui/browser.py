from __future__ import annotations

import posixpath
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ui.icons import icon
from ui.controls import CompactComboBox


class FileBrowser(QWidget):
    browse = Signal(str)
    read_file = Signal(object)
    remove_entry = Signal(object)
    open_file = Signal(object)
    create_directory = Signal(str)

    def __init__(self, root="/", suffix=None, app_name=None, parent=None):
        super().__init__(parent)
        self.root, self.suffix, self.app_name = root, suffix, app_name
        self.current_path = root
        self.known_dirs = {"/", "/ext", "/int", root}
        self.tokens = {'secondary': '#86868f'}
        self.mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        self.mono.setPixelSize(12)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        bar = QHBoxLayout()
        bar.setSpacing(8)
        self.up = QPushButton()
        self.up.setAccessibleName("Übergeordnet")
        self.up.setToolTip("Übergeordneter Ordner")
        self.up.setProperty("role", "ghost")
        self.up.setFixedSize(30, 30)
        self.up.clicked.connect(lambda: self.browse.emit(posixpath.dirname(self.current_path.rstrip('/')) or '/'))
        bar.addWidget(self.up)
        self.path = CompactComboBox()
        self.path.setAccessibleName("Ordner")
        self.path.setMinimumContentsLength(18)
        self.path.setFont(self.mono)
        self.path.addItems(sorted(self.known_dirs))
        self.path.setCurrentText(root)
        self.path.activated.connect(lambda _: self.browse.emit(self.path.currentText()))
        bar.addWidget(self.path, 1)
        self.refresh = QPushButton()
        self.refresh.setAccessibleName("Aktualisieren")
        self.refresh.setToolTip("Ordner aktualisieren")
        self.refresh.setProperty("role", "ghost")
        self.refresh.setFixedSize(30, 30)
        self.refresh.clicked.connect(lambda: self.browse.emit(self.current_path))
        bar.addWidget(self.refresh)
        layout.addLayout(bar)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        listing = QWidget()
        list_layout = QVBoxLayout(listing)
        list_layout.setContentsMargins(0, 0, 12, 0)
        list_layout.setSpacing(8)
        self.table = QTreeWidget()
        self.table.setHeaderLabels(["Name", "Größe"])
        self.table.header().setStretchLastSection(False)
        self.table.headerItem().setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(False)
        self.table.setIconSize(QSize(16, 16))
        self.table.setAccessibleName("Gerätedateien")
        self.table.itemDoubleClicked.connect(self.activate)
        self.table.itemSelectionChanged.connect(self.update_actions)
        list_layout.addWidget(self.table, 1)
        self.summary = QLabel("Noch nicht geladen")
        self.summary.setObjectName("caption")
        self.summary.setWordWrap(True)
        list_layout.addWidget(self.summary)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.read = QPushButton("Inhalt anzeigen")
        self.read.clicked.connect(lambda: self.read_file.emit(self.selected()))
        actions.addWidget(self.read)
        self.open = QPushButton("Am Flipper öffnen")
        self.open.setProperty("role", "primary")
        self.open.setVisible(app_name is not None)
        self.open.clicked.connect(lambda: self.open_file.emit(self.selected()))
        actions.addWidget(self.open)
        actions.addStretch()
        list_layout.addLayout(actions)
        management = QHBoxLayout()
        self.mkdir = QPushButton("Neuer Ordner…")
        self.mkdir.setProperty("role", "ghost")
        self.mkdir.setVisible(app_name is None)
        self.mkdir.clicked.connect(lambda: self.create_directory.emit(self.current_path))
        management.addWidget(self.mkdir)
        self.remove = QPushButton("Löschen…")
        self.remove.setProperty("role", "danger")
        self.remove.setVisible(app_name is None)
        self.remove.clicked.connect(lambda: self.remove_entry.emit(self.selected()))
        management.addWidget(self.remove)
        management.addStretch()
        if app_name is None:
            list_layout.addLayout(management)
        self.splitter.addWidget(listing)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 0, 0, 0)
        preview_layout.setSpacing(8)
        preview_heading = QLabel("Dateivorschau")
        preview_heading.setObjectName("sectionLabel")
        preview_layout.addWidget(preview_heading)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Datei auswählen und\n„Inhalt anzeigen“ klicken.")
        self.preview.setAccessibleName("Dateivorschau")
        self.preview.setFont(self.mono)
        self.preview.document().setMaximumBlockCount(5000)
        preview_layout.addWidget(self.preview)
        self.splitter.addWidget(preview_panel)
        self.splitter.setSizes([440, 280])
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        layout.addWidget(self.splitter, 1)
        self.expert = False
        self.set_theme(self.tokens)
        self.update_actions()

    def set_theme(self, tokens):
        self.tokens = tokens
        self.up.setIcon(icon('up', tokens['secondary']))
        self.refresh.setIcon(icon('refresh', tokens['secondary']))
        for index in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(index)
            entry = item.data(0, Qt.ItemDataRole.UserRole)
            item.setIcon(0, icon('folder' if entry.is_dir else 'file', tokens['secondary']))

    def selected(self):
        item = self.table.currentItem()
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def activate(self, item, column):
        entry = item.data(0, Qt.ItemDataRole.UserRole)
        if entry.is_dir:
            self.browse.emit(entry.path)
        else:
            self.read_file.emit(entry)

    def show_entries(self, path, entries):
        self.current_path = path
        self.known_dirs.add(path)
        self.known_dirs.update(e.path for e in entries if e.is_dir)
        self.path.clear()
        self.path.addItems(sorted(self.known_dirs))
        self.path.setCurrentText(path)
        self.table.clear()
        visible = [e for e in entries if e.is_dir or not self.suffix or e.path.lower().endswith(self.suffix)]
        for entry in sorted(visible, key=lambda e: (not e.is_dir, e.path.casefold())):
            size = "—" if entry.is_dir else f"{entry.size:,} B"
            item = QTreeWidgetItem([posixpath.basename(entry.path), size])
            item.setIcon(0, icon('folder' if entry.is_dir else 'file', self.tokens['secondary']))
            item.setData(0, Qt.ItemDataRole.UserRole, entry)
            item.setFont(1, self.mono)
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.addTopLevelItem(item)
        self.preview.clear()
        self.summary.setText(f"{path} · {len(visible)} Einträge" if visible else f"{path} · Keine passenden Dateien")
        self.update_actions()

    def clear(self):
        self.known_dirs = {"/", "/ext", "/int", self.root}
        self.show_entries(self.root, [])
        self.summary.setText("Nicht verbunden · Dateien nicht geladen")

    def update_actions(self):
        entry = self.selected()
        self.read.setEnabled(bool(entry and not entry.is_dir))
        self.open.setEnabled(bool(entry and not entry.is_dir and self.expert))
        self.open.setToolTip("Startet die passende Geräte-App" if self.expert else "Zum Öffnen Expert-Mode in den Einstellungen aktivieren")
        self.remove.setEnabled(bool(entry))
