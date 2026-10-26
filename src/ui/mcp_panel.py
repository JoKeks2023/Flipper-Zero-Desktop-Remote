"""Native settings for local AI access; client snippets are copied, never installed silently."""
from datetime import datetime
import json
import sys

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QPlainTextEdit, QPushButton, QVBoxLayout,
)
from ui.controls import CompactComboBox


class MCPPanel(QGroupBox):
    preferences_changed = Signal()

    def __init__(self, settings, socket_path):
        super().__init__("KI-Anbindung · MCP")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        self.enabled = QCheckBox("Lokalen MCP-Zugriff aktivieren")
        self.enabled.setChecked(settings.get("mcp_enabled") is True)
        self.enabled.toggled.connect(self.preferences_changed)
        layout.addWidget(self.enabled)
        form = QFormLayout()
        self.permission = CompactComboBox()
        self.permission.setAccessibleName("MCP-Berechtigung")
        self.permission.addItems(["Nur lesen", "Lesen & Bedienen"])
        self.permission.setCurrentIndex(1 if settings.get("mcp_control") else 0)
        self.permission.currentIndexChanged.connect(self.preferences_changed)
        form.addRow("Freigabe", self.permission)
        self.status = QLabel("Ausgeschaltet")
        self.status.setObjectName("subtitle")
        form.addRow("Status", self.status)
        self.last_action = QLabel("Noch keine KI-Anfrage")
        self.last_action.setObjectName("caption")
        self.last_action.setTextFormat(Qt.TextFormat.PlainText)
        form.addRow("Aktivität", self.last_action)
        layout.addLayout(form)
        hint = QLabel("Die App verwaltet die USB-Verbindung. Nur lesen erlaubt Status, Dateivorschau und das aktive Display. Lesen & Bedienen erlaubt zusätzlich Tasten und Live-Ansicht; Tasten können Geräteaktionen auslösen.")
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        row = QHBoxLayout()
        row.addWidget(QLabel("KI-Client"))
        self.client = CompactComboBox()
        self.client.addItems(["Codex", "Claude Desktop / JSON"])
        self.client.setAccessibleName("MCP-Client")
        row.addWidget(self.client)
        row.addStretch()
        self.copy = QPushButton("Konfiguration kopieren")
        self.copy.clicked.connect(self.copy_config)
        row.addWidget(self.copy)
        layout.addLayout(row)
        self.config = QPlainTextEdit()
        self.config.setReadOnly(True)
        self.config.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.config.setAccessibleName("MCP-Client-Konfiguration")
        self.config.setFixedHeight(102)
        layout.addWidget(self.config)
        self.socket_path = str(socket_path)
        self.client.currentIndexChanged.connect(self.update_config)
        self.update_config()

    def update_config(self):
        command = sys.executable
        args = ["-m", "flipper_mcp.server", "--socket", self.socket_path]
        if getattr(sys, "frozen", False):
            args = ["--mcp", "--socket", self.socket_path]
        if self.client.currentIndex() == 0:
            text = "[mcp_servers.flipper]\ncommand = " + json.dumps(command) + "\nargs = " + json.dumps(args) + "\n"
        else:
            text = json.dumps({"mcpServers": {"flipper": {"command": command, "args": args}}}, indent=2, ensure_ascii=False)
        self.config.setPlainText(text)

    def copy_config(self):
        QApplication.clipboard().setText(self.config.toPlainText())
        self.last_action.setText("Konfiguration kopiert · Im KI-Client hinzufügen")

    def activity(self, operation, error=None):
        self.last_action.setText(datetime.now().strftime("%H:%M:%S") + " · " + operation + (" · Fehler" if error else " · Erfolgreich"))
        self.last_action.setToolTip(str(error) if error else "")

    def set_state(self, running, error=None):
        self.permission.setEnabled(self.enabled.isChecked())
        self.status.setText(str(error) if error else ("Bereit · " + self.permission.currentText() if running else "Ausgeschaltet"))
        self.status.setWordWrap(True)
