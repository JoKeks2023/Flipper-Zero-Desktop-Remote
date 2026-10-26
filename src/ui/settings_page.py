"""Settings organized by purpose; advanced setup and credits stay on their own tabs."""
import json
import platform

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QScrollArea, QTabWidget,
    QVBoxLayout, QWidget,
)
from importlib.resources import files

from ui.controls import CompactComboBox
from ui.mcp_panel import MCPPanel

VERSION = "0.2.0"
PROJECT = "https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote"


def text(value, role="subtitle"):
    label = QLabel(value)
    label.setObjectName(role)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label


class SettingsTabs(QTabWidget):
    def __init__(self, window, modules):
        super().__init__()
        self.window = w = window
        self.setObjectName("settingsTabs")
        self.setAccessibleName("Einstellungsbereiche")
        general, layout = self.page("Allgemein")
        layout.addWidget(text("Darstellung & Bedienung", "cardTitle"))
        form = QFormLayout()
        form.setVerticalSpacing(12)
        w.theme = CompactComboBox()
        w.theme.setAccessibleName("Darstellung")
        w.theme.addItems(["System", "Hell", "Dunkel"])
        w.theme.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(w.settings["theme"], 0))
        form.addRow("Darstellung", w.theme)
        w.settings_mode = CompactComboBox()
        w.settings_mode.setAccessibleName("Standard-Bedienmodus")
        w.settings_mode.addItems(["Easy Mode", "Alle Werkzeuge"])
        w.settings_mode.setCurrentIndex(0 if w.settings["easy_mode"] else 1)
        form.addRow("Bedienung", w.settings_mode)
        w.start_module = CompactComboBox()
        names = ["Übersicht", "System", "Flipper bedienen", "Dateien", "Fernbedienungen",
                 "Karten & Tags", "Funk-Signale", "USB-Abläufe", "Makros", "Einstellungen"]
        for name, key in zip(names, modules):
            w.start_module.addItem(name, key)
        w.start_module.setCurrentIndex(max(0, w.start_module.findData(w.settings["start_module"])))
        w.start_module.setToolTip("Easy Mode startet immer mit der Übersicht")
        form.addRow("Startseite", w.start_module)
        w.refresh_interval = CompactComboBox()
        w.refresh_interval.setAccessibleName("Dashboard-Aktualisierung")
        for title, seconds in (("Alle 5 Sekunden", 5), ("Alle 10 Sekunden", 10),
                               ("Alle 30 Sekunden", 30), ("Nur manuell", 0)):
            w.refresh_interval.addItem(title, seconds)
        w.refresh_interval.setCurrentIndex(w.refresh_interval.findData(w.settings["dashboard_refresh_seconds"]))
        form.addRow("Gerätestatus", w.refresh_interval)
        layout.addLayout(form)
        layout.addWidget(text("Änderungen werden sofort gespeichert. Im Easy Mode stehen die häufigen Aufgaben im Vordergrund; unter Alle Werkzeuge sind zusätzlich System und Makros verfügbar."))
        layout.addSpacing(12)
        layout.addWidget(text("Lokale Daten & Diagnose", "cardTitle"))
        layout.addWidget(text("Einstellungen und Makros werden auf diesem Computer gespeichert. Die Diagnose enthält App-, System- und Verbindungsstatus, keine Gerätekennung oder Dateiinhalte."))
        row = QHBoxLayout()
        folder = QPushButton("Datenordner öffnen")
        folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(w.store.base_dir))))
        row.addWidget(folder)
        diagnostics = QPushButton("Diagnose kopieren")
        diagnostics.clicked.connect(self.copy_diagnostics)
        row.addWidget(diagnostics)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

        device, layout = self.page("Gerät")
        layout.addWidget(text("USB-Verbindung", "cardTitle"))
        self.device_status = text("Kein Gerät verbunden")
        layout.addWidget(self.device_status)
        self.ports = CompactComboBox()
        self.ports.setAccessibleName("Gerät in den Einstellungen")
        self.ports.currentTextChanged.connect(lambda value: w.ports.setCurrentText(value))
        form = QFormLayout()
        form.addRow("USB-Gerät", self.ports)
        layout.addLayout(form)
        row = QHBoxLayout()
        self.scan = QPushButton("Geräte suchen")
        self.scan.clicked.connect(w.scan)
        self.connect = QPushButton("Verbinden")
        self.connect.clicked.connect(w.connect_device)
        self.disconnect = QPushButton("Trennen")
        self.disconnect.clicked.connect(w.disconnect_device)
        for button in (self.scan, self.connect, self.disconnect):
            row.addWidget(button)
        row.addStretch()
        layout.addLayout(row)
        w.auto_connect = QCheckBox("Letzten Flipper beim App-Start automatisch verbinden")
        w.auto_connect.setChecked(w.settings["auto_connect"])
        layout.addWidget(w.auto_connect)
        layout.addWidget(text("Verbindet nur den zuletzt verwendeten USB-Port, wenn er gefunden wird. Andere Programme wie qFlipper müssen die Verbindung freigeben."))
        layout.addSpacing(12)
        layout.addWidget(text("Erweiterte Aktionen", "cardTitle"))
        w.expert = QCheckBox("Expert-Mode aktivieren")
        w.expert.setChecked(w.settings["expert_mode"])
        layout.addWidget(w.expert)
        layout.addWidget(text("Erlaubt freie Makros und das Öffnen von Dateien in Geräte-Apps. Dabei können reale Geräteaktionen starten. MCP-Bedienfreigaben werden separat unter KI-Anbindung verwaltet."))
        layout.addStretch()

        ai, layout = self.page("KI-Anbindung")
        w.mcp_panel = MCPPanel(w.settings, w.mcp_bridge.path)
        w.mcp_panel.preferences_changed.connect(w.save_mcp_preferences)
        layout.addWidget(w.mcp_panel)
        layout.addStretch()
        self.about_page()
        w.theme.currentIndexChanged.connect(w.save_preferences)
        w.start_module.currentIndexChanged.connect(w.save_preferences)
        w.refresh_interval.currentIndexChanged.connect(w.save_preferences)
        w.auto_connect.toggled.connect(w.save_preferences)
        w.expert.toggled.connect(w.save_preferences)
        w.settings_mode.currentIndexChanged.connect(w.change_mode)

    def page(self, title):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        self.addTab(scroll, title)
        return content, layout

    def about_page(self):
        page, layout = self.page("Über")
        layout.addWidget(text("Flipper Remote", "deviceHeading"))
        layout.addWidget(text("Version " + VERSION + " · Natives Control Center für macOS und Linux"))
        layout.addWidget(text("Ein Community-Projekt von JoKeks2023. Der Computer ist die Steuerzentrale; der Flipper stellt die Hardware und Gerätefunktionen bereit."))
        links = QLabel(f'<a href="{PROJECT}">Projekt</a> · <a href="{PROJECT}/issues/new">Fehler melden</a> · <a href="{PROJECT}/releases">Veröffentlichungen</a>')
        links.setOpenExternalLinks(True)
        layout.addWidget(links)
        layout.addSpacing(8)
        layout.addWidget(text("Daten & Privatsphäre", "cardTitle"))
        layout.addWidget(text("Die App enthält keine Nutzungsanalyse. Einstellungen und Makros bleiben lokal. Bei MCP-Anfragen gehen die angeforderten Geräteinformationen an deinen KI-Client; dieser bestimmt die Weitergabe an ein Modell."))
        layout.addSpacing(8)
        layout.addWidget(text("Credits", "cardTitle"))
        for name, contribution in (
            ("Flipper Devices", "Flipper Zero und das öffentliche Geräteprotokoll"),
            ("Momentum", "Firmware und Community-Erweiterungen"),
            ("Qt / PySide6 & Shiboken", "Native Oberfläche und Python-Anbindung"),
            ("pySerial", "Serielle USB-Kommunikation"),
            ("Model Context Protocol", "Offizielles Python-SDK für die KI-Anbindung"),
            ("Mitwirkende & Community", "Fehlerberichte, Ideen und Beiträge"),
        ):
            layout.addWidget(text(name + " · " + contribution))
        layout.addSpacing(8)
        layout.addWidget(text("© 2026 JoKeks2023 · Projektlizenz: MIT. Abhängigkeiten behalten ihre eigenen Lizenzen.", "caption"))
        row = QHBoxLayout()
        notices = QPushButton("Lizenzen & Open-Source-Hinweise")
        notices.clicked.connect(self.show_licenses)
        row.addWidget(notices)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()

    def show_licenses(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Lizenzen & Open-Source-Hinweise")
        dialog.resize(720, 520)
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        for title, name in (("Projekt · MIT", "LICENSE.txt"), ("Abhängigkeiten", "THIRD_PARTY_NOTICES.txt")):
            content = QPlainTextEdit()
            content.setReadOnly(True)
            content.setPlainText(files("ui").joinpath("legal", name).read_text(encoding="utf-8"))
            tabs.addTab(content, title)
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Schließen")
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def copy_diagnostics(self):
        w = self.window
        data = {"app": "Flipper Remote", "version": VERSION, "system": platform.system(),
                "system_version": platform.release(), "architecture": platform.machine(),
                "python": platform.python_version(), "pyside": PYSIDE_VERSION,
                "connected": w.connected, "live_view": w.rpc.is_connected,
                "mcp_enabled": w.mcp_bridge.running, "mcp_control": w.settings["mcp_control"]}
        QApplication.clipboard().setText(json.dumps(data, indent=2))
        w.statusBar().showMessage("Diagnose kopiert · Enthält keine Gerätekennung oder Dateiinhalte", 6000)

    def sync_ports(self):
        w = self.window
        self.ports.blockSignals(True)
        self.ports.clear()
        self.ports.addItems([w.ports.itemText(i) for i in range(w.ports.count())])
        self.ports.setCurrentText(w.ports.currentText())
        self.ports.blockSignals(False)

    def update_device(self):
        w = self.window
        connected = w.connected
        self.device_status.setText((w.device_label.text() + " · USB verbunden") if connected else "Kein Flipper verbunden")
        self.ports.setEnabled(not connected and not w.busy)
        self.scan.setEnabled(not w.busy and not connected)
        self.connect.setEnabled(not w.busy and not connected and self.ports.count() > 0)
        self.disconnect.setEnabled(connected)
