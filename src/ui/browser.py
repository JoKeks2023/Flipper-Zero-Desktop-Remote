from __future__ import annotations

import posixpath
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.storage import StorageEntry


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
        layout = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.path = QComboBox()
        self.path.setAccessibleName("Ordner")
        self.path.setMinimumContentsLength(25)
        self.path.addItems(sorted(self.known_dirs))
        self.path.setCurrentText(root)
        self.path.activated.connect(lambda _: self.browse.emit(self.path.currentText()))
        bar.addWidget(QLabel("Ordner"))
        bar.addWidget(self.path, 1)
        self.up = QPushButton("Übergeordnet")
        self.up.clicked.connect(lambda: self.browse.emit(posixpath.dirname(self.current_path.rstrip('/')) or '/'))
        bar.addWidget(self.up)
        self.refresh = QPushButton("Aktualisieren")
        self.refresh.clicked.connect(lambda: self.browse.emit(self.current_path))
        bar.addWidget(self.refresh)
        layout.addLayout(bar)
        self.table = QTreeWidget()
        self.table.setHeaderLabels(["Name", "Typ", "Größe"])
        self.table.setColumnWidth(0, 330)
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(True)
        self.table.setAccessibleName("Gerätedateien")
        self.table.itemDoubleClicked.connect(self.activate)
        self.table.itemSelectionChanged.connect(self.update_actions)
        layout.addWidget(self.table, 2)
        self.summary = QLabel("Noch nicht geladen · Aktualisieren lädt den Geräteordner")
        layout.addWidget(self.summary)
        actions = QHBoxLayout()
        self.read = QPushButton("Inhalt anzeigen")
        self.read.clicked.connect(lambda: self.read_file.emit(self.selected()))
        actions.addWidget(self.read)
        self.open = QPushButton("Am Flipper öffnen")
        self.open.setVisible(app_name is not None)
        self.open.clicked.connect(lambda: self.open_file.emit(self.selected()))
        actions.addWidget(self.open)
        self.mkdir = QPushButton("Neuer Ordner…")
        self.mkdir.setVisible(app_name is None)
        self.mkdir.clicked.connect(lambda: self.create_directory.emit(self.current_path))
        actions.addWidget(self.mkdir)
        self.remove = QPushButton("Löschen…")
        self.remove.setVisible(app_name is None)
        self.remove.clicked.connect(lambda: self.remove_entry.emit(self.selected()))
        actions.addWidget(self.remove)
        actions.addStretch()
        layout.addLayout(actions)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Datei auswählen und „Inhalt anzeigen“ klicken.")
        self.preview.setAccessibleName("Dateivorschau")
        self.preview.document().setMaximumBlockCount(5000)
        layout.addWidget(self.preview, 1)
        self.expert = False
        self.update_actions()

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
            item = QTreeWidgetItem([posixpath.basename(entry.path), "Ordner" if entry.is_dir else "Datei", "" if entry.is_dir else f"{entry.size:,} B"])
            item.setData(0, Qt.ItemDataRole.UserRole, entry)
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
        self.remove.setEnabled(bool(entry))
