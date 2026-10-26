from __future__ import annotations

import posixpath
import shlex
import sys
import threading

from PySide6.QtCore import Qt, QSize, QThreadPool, QTimer
from PySide6.QtGui import QAction, QColor, QFontDatabase, QPalette, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDockWidget, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QFrame, QProgressBar, QScrollArea, QStyle, QSizePolicy,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
    QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.connection_manager import scan_flipper_ports
from core.flipper_api import FlipperAPI
from core.serial_client import SerialClient
from core.rpc_display import RpcDisplay
from core.storage import quote_path
from core.device_status import read_device_status
from persistence.config_store import ConfigStore
from ui.browser import FileBrowser
from ui.jobs import Job
from ui.screen import ScreenView
from ui.sidebar import Sidebar
from ui.icons import icon, MODULE_ICONS
from ui.action_row import ActionRow
from ui.controls import CompactComboBox
from ui.dashboard import DeviceDashboard
from ui.theme import colors, palette as theme_palette, stylesheet

APP_NAME = "Flipper Zero Desktop Remote"
MODULES = ["Control Center", "System", "Remote", "Storage", "Infrared", "NFC/RFID", "Sub-GHz", "BadUSB", "Makros", "Einstellungen"]


def macro_allowed(command: str, expert: bool) -> bool:
    if any(ord(c) < 32 or ord(c) == 127 for c in command):
        return False
    if expert:
        return True
    if any(c in command for c in "|;&"):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if not parts:
        return False
    if parts[0] in {"device_info", "help", "uptime", "free"}:
        return len(parts) == 1
    if parts == ["loader", "info"]:
        return True
    if len(parts) == 3 and parts[:2] in [["storage", sub] for sub in ("list", "read", "stat", "info")]:
        return parts[2].startswith("/")
    return (len(parts) == 4 and parts[:2] == ["input", "send"]
            and parts[2] in {"up", "down", "left", "right", "ok", "back"}
            and parts[3] in {"short", "long", "press", "release"})


class MainWindow(QMainWindow):
    def __init__(self, store=None, client=None, scan_ports=scan_flipper_ports):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1080, 680)
        self.setMinimumSize(960, 600)
        self.store = store or ConfigStore(APP_NAME)
        self.settings = self.store.load_settings()
        self.macros = self.store.load_macros()
        self.client = client or SerialClient()
        self.api = FlipperAPI(self.client.send_command)
        self.rpc = RpcDisplay()
        self.scan_ports = scan_ports
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.jobs = set()
        self.busy = False
        self.generation = 0
        self.closing = threading.Event()
        self.was_connected = False
        self.connected_port = ""
        self.device_description = "Flipper anschließen und loslegen"
        self.device_controls = []
        self.browsers = []
        self._system_palette = QPalette(QApplication.palette())
        self._build()
        self._refresh_macros()
        self._apply_settings()
        self._apply_mode()
        self.scan()
        start = "Control Center" if self.settings.get("easy_mode", True) else self.settings.get("start_module", "Control Center")
        self.nav.setCurrentRow(MODULES.index(start) if start in MODULES else 0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._pump)
        self.timer.start(100)
        self.dashboard_timer = QTimer(self)
        self.dashboard_timer.timeout.connect(self._poll_dashboard)
        self.dashboard_timer.start(10_000)
        self._update_state()

    def _build(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        shell = QFrame()
        shell.setObjectName("sidebarShell")
        shell.setFixedWidth(196)
        side = QVBoxLayout(shell)
        side.setContentsMargins(12, 20, 12, 12)
        side.setSpacing(16)
        identity = QHBoxLayout()
        identity.setSpacing(10)
        self.brand_mark = QLabel()
        self.brand_mark.setFixedSize(28, 28)
        identity.addWidget(self.brand_mark)
        names = QVBoxLayout()
        names.setSpacing(2)
        brand = QLabel("Flipper Remote")
        brand.setObjectName("brand")
        caption = QLabel("Control Center")
        caption.setObjectName("brandCaption")
        names.addWidget(brand)
        names.addWidget(caption)
        identity.addLayout(names)
        side.addLayout(identity)
        self.nav = Sidebar()
        self.nav.setObjectName("sidebar")
        self.nav.addItems(MODULES)
        self.nav.setSpacing(2)
        self.nav.setAccessibleName("Module")
        side.addWidget(self.nav, 1)
        mode_caption = QLabel("Bedienung")
        mode_caption.setObjectName("caption")
        side.addWidget(mode_caption)
        self.mode = CompactComboBox()
        self.mode.addItems(["Easy Mode", "Alle Werkzeuge"])
        self.mode.setAccessibleName("Bedienmodus")
        self.mode.setCurrentIndex(0 if self.settings.get("easy_mode", True) else 1)
        self.mode.currentIndexChanged.connect(self.change_mode)
        side.addWidget(self.mode)
        root_layout.addWidget(shell)
        workspace = QWidget()
        workspace.setObjectName("workspace")
        main_layout = QVBoxLayout(workspace)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(52)
        top = QHBoxLayout(toolbar)
        top.setContentsMargins(24, 8, 24, 8)
        top.setSpacing(8)
        self.connection_dot = QLabel("●")
        self.connection_dot.setObjectName("connectionDot")
        self.device_label = QLabel("Kein Gerät")
        self.device_label.setObjectName("deviceName")
        self.connection_label = QLabel("Nicht verbunden")
        self.connection_label.setObjectName("connectionStatus")
        top.addWidget(self.connection_dot)
        top.addWidget(self.device_label)
        top.addWidget(self.connection_label)
        top.addStretch()
        self.ports = CompactComboBox()
        self.ports.setAccessibleName("USB-Port")
        self.ports.setMaximumWidth(260)
        self.ports.setMinimumContentsLength(16)
        self.scan_button = QPushButton("Suchen")
        self.scan_button.setProperty("role", "ghost")
        self.scan_button.clicked.connect(self.scan)
        self.connect_button = QPushButton("Verbinden")
        self.connect_button.setProperty("role", "primary")
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button = QPushButton("Trennen")
        self.disconnect_button.setProperty("role", "ghost")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.stop_button = QPushButton("Abbrechen")
        self.stop_button.setProperty("role", "ghost")
        self.stop_button.setToolTip("Laufenden CLI-Befehl mit Strg+C abbrechen")
        self.stop_button.clicked.connect(self.interrupt)
        for widget in [self.ports, self.scan_button, self.connect_button, self.disconnect_button, self.stop_button]:
            top.addWidget(widget)
        main_layout.addWidget(toolbar)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._home_page())
        self.stack.addWidget(self._system_page())
        self.stack.addWidget(self._remote_page())
        self.stack.addWidget(self._browser_page("Storage", "/"))
        self.stack.addWidget(self._browser_page("Infrared", "/ext/infrared", ".ir", "Infrared"))
        self.stack.addWidget(self._browser_page("NFC/RFID", "/ext/nfc", ".nfc", "NFC"))
        self.stack.addWidget(self._browser_page("Sub-GHz", "/ext/subghz", ".sub", "Sub-GHz"))
        self.stack.addWidget(self._browser_page("BadUSB", "/ext/badusb", ".txt", "Bad KB"))
        self.stack.addWidget(self._macros_page())
        self.stack.addWidget(self._settings_page())
        self.nav.currentRowChanged.connect(self._select_module)
        main_layout.addWidget(self.stack, 1)
        root_layout.addWidget(workspace, 1)
        self.setCentralWidget(root)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setAccessibleName("Aktivitätsprotokoll")
        self.log.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.log.document().setMaximumBlockCount(2000)
        dock = QDockWidget("Technisches Protokoll", self)
        self.log_dock = dock
        dock.setWidget(self.log)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.setMinimumHeight(100)
        self.resizeDocks([dock], [150], Qt.Orientation.Vertical)
        destinations = self.menuBar().addMenu("Gehe zu")
        for index, name in enumerate(MODULES):
            action = QAction(name, self)
            if index < 9:
                action.setShortcut(QKeySequence(f"Ctrl+{index + 1}"))
            action.triggered.connect(lambda checked=False, i=index: self.nav.setCurrentRow(i))
            destinations.addAction(action)
        view = self.menuBar().addMenu("Ansicht")
        view.addAction(dock.toggleViewAction())
        clear = QAction("Protokoll leeren", self)
        clear.triggered.connect(self.log.clear)
        view.addAction(clear)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(110)
        self.progress.setMaximumHeight(5)
        self.progress.hide()
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().showMessage("Bereit · Flipper per USB verbinden")

    def _page(self, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)
        label = QLabel(title)
        label.setObjectName("pageTitle")
        label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(label)
        if subtitle:
            hint = QLabel(subtitle)
            hint.setWordWrap(True)
            hint.setObjectName("subtitle")
            hint.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            layout.addWidget(hint)
        return page, layout

    def _button(self, label, callback, layout, device=True):
        button = QPushButton(label)
        button.clicked.connect(callback)
        layout.addWidget(button)
        if device:
            self.device_controls.append(button)
        return button

    def _home_page(self):
        page, layout = self._page("Übersicht", "")
        layout.setSpacing(8)
        self.dashboard = DeviceDashboard()
        self.dashboard.refresh_requested.connect(self.refresh_dashboard)
        self.dashboard.remote_requested.connect(lambda: self.nav.setCurrentRow(MODULES.index("Remote")))
        layout.addWidget(self.dashboard)
        label = QLabel("Werkzeuge")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)
        self.home_rows = []
        rows = QWidget()
        row_layout = QGridLayout(rows)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setHorizontalSpacing(24)
        row_layout.setVerticalSpacing(0)
        tasks = [
            ("Live-Bedienung", "Geräte-Display, Navigation und Tastatur", "Remote", "remote"),
            ("Fernbedienungen", "IR-Dateien auf der SD-Karte", "Infrared", "infrared"),
            ("Dateien", "Ordner, Textvorschau und Speicherverwaltung", "Storage", "folder"),
            ("Karten & Tags", "Gespeicherte NFC-Dateien", "NFC/RFID", "nfc"),
            ("Funk-Signale", "Gespeicherte Sub-GHz-Dateien", "Sub-GHz", "radio"),
            ("USB-Abläufe", "Gespeicherte Skripte", "BadUSB", "usb"),
        ]
        for index, (title, description, module, symbol) in enumerate(tasks):
            row = ActionRow(title, description, symbol)
            row.clicked.connect(lambda checked=False, name=module: self.nav.setCurrentRow(MODULES.index(name)))
            row_layout.addWidget(row, index // 2, index % 2)
            self.home_rows.append(row)
        row_layout.setColumnStretch(0, 1)
        row_layout.setColumnStretch(1, 1)
        layout.addWidget(rows)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    def change_mode(self, index):
        self.settings["easy_mode"] = index == 0
        self._save(self.store.save_settings, self.settings)
        self._apply_mode()

    def _apply_mode(self):
        easy = self.settings.get("easy_mode", True)
        for index, name in enumerate(MODULES):
            self.nav.item(index).setHidden(easy and name in {"System", "Makros"})
        self.nav.sections[8].setVisible(not easy)
        easy_names = {"Control Center": "Übersicht", "Remote": "Flipper bedienen", "Storage": "Dateien", "Infrared": "Fernbedienungen", "NFC/RFID": "Karten & Tags", "Sub-GHz": "Funk-Signale", "BadUSB": "USB-Abläufe"}
        for index, name in enumerate(MODULES):
            self.nav.item(index).setText(easy_names.get(name, name) if easy else name)
            title = self.stack.widget(index).findChild(QLabel, "pageTitle")
            if title and name in easy_names:
                title.setText(easy_names[name] if easy else name)
        self.log_dock.setVisible(not easy)
        self.ports.setVisible(not easy or self.ports.count() > 1)
        self.scan_button.setVisible(not easy)
        if easy and self.nav.currentRow() >= 0 and MODULES[self.nav.currentRow()] in {"System", "Makros"}:
            self.nav.setCurrentRow(0)

    @property
    def connected(self):
        return self.client.is_connected or self.rpc.is_connected

    def _ensure_cli(self):
        if self.closing.is_set() or getattr(self, "cancel_macro", threading.Event()).is_set():
            raise InterruptedError("Aktion abgebrochen")
        if self.rpc.is_connected:
            self.rpc.disconnect()
            self.client.connect(self.connected_port)
        if not self.client.is_connected:
            raise RuntimeError("Kein Flipper verbunden")

    def toggle_live(self):
        if self.rpc.is_connected:
            def stop():
                self._ensure_cli()
            self.submit("Live-Ansicht beenden", stop, lambda _: self.screen.clear())
        else:
            def start():
                self.client.disconnect()
                try:
                    self.rpc.connect(self.connected_port)
                    if self.closing.is_set() or self.cancel_macro.is_set():
                        self.rpc.disconnect()
                        raise InterruptedError("Aktion abgebrochen")
                except Exception:
                    if not self.closing.is_set() and not self.cancel_macro.is_set():
                        self.client.connect(self.connected_port)
                    raise
            self.submit("Live-Ansicht starten", start)

    def send_key(self, key):
        long = self.long_press.isChecked()
        if self.rpc.is_connected:
            self.submit("Taste senden", lambda: self.rpc.input(key, long))
        else:
            self.command(f"input send {key} {'long' if long else 'short'}")

    def _system_page(self):
        page, layout = self._page("System", "Geräteinformationen und Firmware vom verbundenen Flipper.")
        row = QHBoxLayout()
        self._button("Geräteinfo laden", lambda: self.command("device_info", self._show_info), row)
        self._button("Laufende App", lambda: self.command("loader info", self._show_output), row)
        self._button("Neu starten…", self.reboot, row)
        row.addStretch()
        layout.addLayout(row)
        self.info = QTreeWidget()
        self.info.setHeaderLabels(["Eigenschaft", "Wert"])
        self.info.setRootIsDecorated(False)
        self.info.setColumnWidth(0, 280)
        self.info.setAccessibleName("Geräteinformationen")
        layout.addWidget(self.info)
        return page

    def _remote_page(self):
        page, layout = self._page("Remote", "Sieh das Geräte-Display live und bediene den Flipper mit Tasten oder deiner Tastatur.")
        host = QWidget()
        host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        host.setMaximumHeight(320)
        body = QHBoxLayout(host)
        body.setContentsMargins(0, 8, 0, 0)
        body.setSpacing(24)
        display = QVBoxLayout()
        self.screen = ScreenView()
        self.screen.setFixedHeight(256)
        display.setSpacing(8)
        display.addWidget(self.screen)
        live_row = QHBoxLayout()
        self.live_button = QPushButton("Live-Ansicht starten")
        self.live_button.setProperty("role", "primary")
        self.live_button.clicked.connect(self.toggle_live)
        self.device_controls.append(self.live_button)
        live_row.addWidget(self.live_button)
        self.live_status = QLabel("Display noch nicht verbunden")
        self.live_status.setObjectName("caption")
        live_row.addWidget(self.live_status)
        live_row.addStretch()
        display.addLayout(live_row)
        body.addLayout(display, 3)
        controls = QVBoxLayout()
        group = QGroupBox("Tasten")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 4, 0, 0)
        for label, key, row, column in [("↑", "up", 0, 1), ("←", "left", 1, 0), ("OK", "ok", 1, 1), ("→", "right", 1, 2), ("↓", "down", 2, 1), ("Zurück", "back", 3, 1)]:
            button = QPushButton(label)
            button.setAccessibleName({"up": "Nach oben", "down": "Nach unten", "left": "Nach links", "right": "Nach rechts", "ok": "OK", "back": "Zurück"}[key])
            button.setObjectName("remoteKey" if key != "back" else "remoteBack")
            button.setProperty("center", key == "ok")
            button.setFixedSize(44, 40) if key != "back" else button.setFixedSize(112, 28)
            button.clicked.connect(lambda checked=False, k=key: self.send_key(k))
            if key == "back":
                grid.addWidget(button, row, 0, 1, 3, Qt.AlignmentFlag.AlignHCenter)
            else:
                grid.addWidget(button, row, column)
            self.device_controls.append(button)
        controls.addWidget(group)
        self.long_press = QCheckBox("Langer Tastendruck")
        controls.addWidget(self.long_press)
        keyboard_hint = QLabel("Pfeiltasten · Enter · Escape")
        keyboard_hint.setObjectName("subtitle")
        controls.addWidget(keyboard_hint)
        controls.addStretch()
        body.addLayout(controls, 1)
        layout.addWidget(host)
        layout.addStretch()
        for shortcut, key in [("Up", "up"), ("Down", "down"), ("Left", "left"), ("Right", "right"), ("Return", "ok"), ("Backspace", "back"), ("Escape", "back")]:
            binding = QShortcut(QKeySequence(shortcut), page)
            binding.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            binding.setAutoRepeat(False)
            binding.activated.connect(lambda k=key: self.send_key(k))
        return page

    def _browser_page(self, title, root, suffix=None, app_name=None):
        subtitle = "Dateien auswählen und auf dem Flipper öffnen." if app_name else "Ordner öffnen, Dateien ansehen und verwalten."
        page, layout = self._page(title, subtitle)
        browser = FileBrowser(root, suffix, app_name)
        browser.browse.connect(lambda path, b=browser: self.browse(b, path))
        browser.read_file.connect(lambda entry, b=browser: self.read_file(b, entry))
        browser.remove_entry.connect(lambda entry, b=browser: self.remove_entry(b, entry))
        browser.create_directory.connect(lambda path, b=browser: self.mkdir(b, path))
        browser.open_file.connect(lambda entry, b=browser: self.open_file(b, entry))
        self.browsers.append(browser)
        self.device_controls.append(browser)
        layout.addWidget(browser)
        return page

    def _macros_page(self):
        page, layout = self._page("Makros", "Befehle laufen nacheinander. Der nächste startet erst nach der Geräteantwort. Abbrechen stoppt die Sequenz.")
        self.macro_select = CompactComboBox()
        self.macro_select.setAccessibleName("Gespeichertes Makro")
        self.macro_select.currentTextChanged.connect(self.load_macro)
        layout.addWidget(self.macro_select)
        self.macro_name = QLineEdit()
        self.macro_name.setPlaceholderText("Name für das Makro")
        self.macro_name.setAccessibleName("Makro-Name")
        layout.addWidget(self.macro_name)
        self.macro_commands = QPlainTextEdit()
        self.macro_commands.setPlaceholderText("Ein CLI-Befehl pro Zeile")
        self.macro_commands.setAccessibleName("Makro-Befehle")
        layout.addWidget(self.macro_commands)
        row = QHBoxLayout()
        self._button("Speichern", self.save_macro, row, False)
        self._button("Neu", self.new_macro, row, False)
        self._button("Löschen…", self.delete_macro, row, False)
        self._button("Ausführen", self.run_macro, row)
        row.addStretch()
        layout.addLayout(row)
        return page

    def _settings_page(self):
        page, layout = self._page("Einstellungen", "Einstellungen und Makros bleiben lokal auf diesem Computer.")
        form = QFormLayout()
        self.theme = CompactComboBox()
        self.theme.addItems(["System", "Hell", "Dunkel"])
        self.theme.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(self.settings.get("theme"), 0))
        self.theme.currentIndexChanged.connect(self.save_preferences)
        form.addRow("Darstellung", self.theme)
        self.start_module = CompactComboBox()
        self.start_module.addItems(MODULES)
        self.start_module.setCurrentText(self.settings.get("start_module", "System"))
        self.start_module.currentTextChanged.connect(self.save_preferences)
        form.addRow("Startmodul", self.start_module)
        self.expert = QCheckBox("Expert-Mode")
        self.expert.setChecked(self.settings.get("expert_mode") is True)
        self.expert.toggled.connect(self.save_preferences)
        form.addRow("Erweiterte Aktionen", self.expert)
        layout.addLayout(form)
        hint = QLabel("Expert-Mode erlaubt das Öffnen von IR/NFC/Sub-GHz/BadUSB-Dateien in der Geräte-App sowie freie CLI-Makros. Ohne Expert-Mode sind Makros auf lesende Abfragen und Navigation begrenzt.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        path = QLabel(f"Lokale Daten: {self.store.base_dir}")
        path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path.setWordWrap(True)
        layout.addWidget(path)
        layout.addStretch()
        return page

    def _select_module(self, index):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self._poll_dashboard()
        if 3 <= index <= 7 and self.connected and not self.busy:
            browser = self.browsers[index - 3]
            self.browse(browser, browser.current_path)

    def _apply_settings(self):
        mode = self.settings.get("theme", "system")
        dark = mode == "dark" or (mode == "system" and self._system_palette.color(QPalette.ColorRole.Window).lightness() < 128)
        self.tokens = colors(dark)
        QApplication.setPalette(theme_palette(self.tokens))
        self.setStyleSheet(stylesheet(self.tokens))
        self.brand_mark.setPixmap(icon("device", self.tokens['accent']).pixmap(QSize(28, 28)))
        for index, symbol in enumerate(MODULE_ICONS):
            self.nav.item(index).setIcon(icon(symbol, self.tokens['secondary'], self.tokens['accent']))
            self.nav.item(index).setIconSize(QSize(16, 16))
        for row in self.home_rows:
            row.tokens = self.tokens
            row.update()
        self.screen.stage_color = self.tokens['surface']
        self.screen.update()
        for browser in self.browsers:
            browser.expert = self.settings.get("expert_mode") is True
            browser.set_theme(self.tokens)
            browser.update_actions()
        self._update_connection_identity()

    def _update_connection_identity(self):
        self.connection_dot.setStyleSheet("color: " + ("#2ea043" if self.connected else self.tokens['muted']) + ";")

    def save_preferences(self, *args):
        self.settings.update(theme=["system", "light", "dark"][self.theme.currentIndex()], start_module=self.start_module.currentText(), expert_mode=self.expert.isChecked())
        self._save(self.store.save_settings, self.settings)
        self._apply_settings()

    def _save(self, writer, value):
        try:
            writer(value)
            return True
        except OSError as exc:
            self._error(f"Lokale Daten konnten nicht gespeichert werden: {exc}")
            return False

    def scan(self):
        try:
            ports = self.scan_ports()
        except Exception as exc:
            self._error(str(exc))
            return
        selected = self.ports.currentText() or self.settings.get("last_port", "")
        self.ports.clear()
        self.ports.addItems(ports)
        if selected in ports:
            self.ports.setCurrentText(selected)
        self._apply_mode()
        self._update_state()

    def submit(self, label, work, success=None, require_connection=True):
        if self.busy or self.closing.is_set():
            return False
        if require_connection and not self.connected:
            self._error("Kein Flipper verbunden")
            return False
        self.busy = True
        self.cancel_macro = threading.Event()
        generation = self.generation
        job = Job(work)
        self.jobs.add(job)
        def finished(result, error):
            self.jobs.discard(job)
            self.busy = False
            if self.closing.is_set():
                self.rpc.disconnect()
                self.client.disconnect()
                self.close()
                return
            if generation == self.generation:
                if error:
                    self._error(str(error))
                else:
                    self.statusBar().showMessage(f"Abgeschlossen: {label}", 6000)
                    if success:
                        success(result)
            self._update_state()
        job.signals.finished.connect(finished, Qt.ConnectionType.QueuedConnection)
        self.statusBar().showMessage(label + " …")
        self._update_state()
        self.pool.start(job)
        return True

    def command(self, command, success=None):
        def work():
            self._ensure_cli()
            return self.client.send_command(command)
        labels = {"device_info": "Geräteinformationen laden", "storage read": "Dateivorschau laden",
                  "storage mkdir": "Ordner erstellen", "storage remove": "Datei löschen",
                  "input send": "Taste senden", "loader open": "Geräte-App öffnen", "loader info": "Laufende Geräte-App"}
        label = next((value for prefix, value in labels.items() if command.startswith(prefix)), "Befehl ausführen")
        return self.submit(label, work, success)

    def connect_device(self):
        if not self.ports.currentText():
            self.scan()
        port = self.ports.currentText()
        if not port:
            self._error("Kein USB-Port gefunden. Flipper anschließen und Suchen klicken.")
            return
        def work():
            try:
                self.client.connect(port)
                if self.closing.is_set() or self.cancel_macro.is_set():
                    self.client.disconnect()
                    raise InterruptedError("Verbindung abgebrochen")
                return read_device_status(self.client.send_command, self.cancel_macro.is_set)
            except Exception:
                self.client.disconnect()
                raise
        def connected(status):
            self.connected_port = port
            self.settings["last_port"] = port
            self._save(self.store.save_settings, self.settings)
            self._show_status(status)
        self.submit("Flipper verbinden", work, connected, require_connection=False)

    def _poll_dashboard(self):
        if self.stack.currentIndex() == 0 and self.client.is_connected and not self.rpc.is_connected and not self.busy:
            self.refresh_dashboard()

    def refresh_dashboard(self):
        # Telemetry never switches the serial owner or interrupts a live screen.
        if not self.client.is_connected or self.rpc.is_connected:
            return False
        return self.submit("Gerätestatus aktualisieren",
                           lambda: read_device_status(self.client.send_command, self.cancel_macro.is_set),
                           self._show_status)

    def _show_status(self, status):
        self._show_info("\n".join(f"{key}: {value}" for key, value in status.device.items()))
        self.dashboard.show_status(status)
        if not self.client.is_connected:
            self._clear_device()

    def disconnect_device(self):
        self.generation += 1
        if hasattr(self, "cancel_macro"):
            self.cancel_macro.set()
        self.rpc.disconnect(graceful=False)
        self.client.disconnect()
        self._clear_device()
        self._update_state()
        self.statusBar().showMessage("Verbindung getrennt")

    def interrupt(self):
        if hasattr(self, "cancel_macro"):
            self.cancel_macro.set()
        try:
            if self.rpc.is_connected:
                self.rpc.disconnect(graceful=False)
            else:
                self.client.interrupt()
            self.statusBar().showMessage("Abbruch angefordert …")
        except Exception as exc:
            self._error(str(exc))

    def _show_info(self, response):
        self.info.clear()
        values = {}
        for line in response.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
                self.info.addTopLevelItem(QTreeWidgetItem([key.strip(), value.strip()]))
        self.device_label.setText(values.get("hardware_name", "Flipper Zero"))
        self.device_description = " · ".join(filter(None, [values.get("hardware_name"), values.get("firmware_origin_fork"), values.get("firmware_version"), "USB verbunden"]))

    def _show_output(self, response):
        if response:
            self.statusBar().showMessage(response[:240], 15000)

    def browse(self, browser, path):
        def loaded(entries):
            browser.show_entries(path, entries)
        def work():
            self._ensure_cli()
            return self.api.list_directory(path)
        self.submit(f"Ordner laden: {path}", work, loaded)

    def read_file(self, browser, entry):
        if not entry or entry.is_dir:
            return
        if entry.size is not None and entry.size > 128_000:
            self._error("Vorschau auf 128 KB begrenzt. Bitte eine kleinere Datei wählen.")
            return
        self.command(f"storage read {quote_path(entry.path)}", browser.preview.setPlainText)

    def remove_entry(self, browser, entry):
        if not entry or not self._confirm("Vom Flipper löschen?", f"{entry.path}\n\nDiese Löschung kann nicht rückgängig gemacht werden."):
            return
        self.command(f"storage remove {quote_path(entry.path)}", lambda _: self.browse(browser, browser.current_path))

    def mkdir(self, browser, path):
        name, accepted = QInputDialog.getText(self, "Neuer Ordner", "Name im aktuellen Ordner:")
        if not accepted:
            return
        if not name.strip() or name in {".", ".."} or any(c in name for c in '/"\r\n\x00'):
            self._error("Bitte einen Ordnernamen ohne Schrägstrich, Anführungszeichen oder Steuerzeichen angeben.")
            return
        target = posixpath.join(path, name.strip())
        self.command(f"storage mkdir {quote_path(target)}", lambda _: self.browse(browser, path))

    def open_file(self, browser, entry):
        if not entry or not self.expert.isChecked():
            self._error("Zum Öffnen auf dem Flipper ist Expert-Mode erforderlich.")
            return
        if not self._confirm("Datei auf dem Flipper öffnen?", f"{entry.path}\n\nStartet {browser.app_name} auf dem Gerät. Die Geräte-App kann je nach Dateityp direkt Aktionen ausführen."):
            return
        # loader passes the remainder as the application's path argument (not CLI tokens).
        def opened(_):
            self.nav.setCurrentRow(MODULES.index("Remote"))
            self.toggle_live()
        self.command(f'loader open "{browser.app_name}" {entry.path}', opened)

    def reboot(self):
        if not self._confirm("Flipper neu starten?", "Die USB-Verbindung wird dabei getrennt."):
            return
        def work():
            self._ensure_cli()
            try:
                self.client.send_command("power reboot", timeout=3)
            except (TimeoutError, RuntimeError):
                pass  # A reboot can disconnect before returning a prompt.
            finally:
                self.client.disconnect()
        self.submit("Neustart angefordert", work, lambda _: self._clear_device())

    def _refresh_macros(self, selected=None):
        self.macro_select.blockSignals(True)
        self.macro_select.clear()
        self.macro_select.addItems(sorted(self.macros))
        if selected in self.macros:
            self.macro_select.setCurrentText(selected)
        self.macro_select.blockSignals(False)
        self.load_macro(self.macro_select.currentText())

    def load_macro(self, name):
        self.macro_name.setText(name)
        self.macro_commands.setPlainText("\n".join(self.macros.get(name, [])))

    def new_macro(self):
        self.macro_select.setCurrentIndex(-1)
        self.macro_name.clear()
        self.macro_commands.clear()
        self.macro_name.setFocus()

    def save_macro(self):
        name = self.macro_name.text().strip()
        commands = [line.strip() for line in self.macro_commands.toPlainText().splitlines() if line.strip()]
        if not name or not commands:
            self._error("Name und mindestens ein Befehl sind erforderlich.")
            return
        if name in self.macros and not self._confirm("Makro überschreiben?", name):
            return
        updated = {**self.macros, name: commands}
        if self._save(self.store.save_macros, updated):
            self.macros = updated
            self._refresh_macros(name)

    def delete_macro(self):
        name = self.macro_select.currentText()
        if name not in self.macros or not self._confirm("Makro löschen?", name):
            return
        updated = {key: value for key, value in self.macros.items() if key != name}
        if self._save(self.store.save_macros, updated):
            self.macros = updated
            self._refresh_macros()

    def run_macro(self):
        commands = [line.strip() for line in self.macro_commands.toPlainText().splitlines() if line.strip()]
        if not commands:
            self._error("Das Makro ist leer.")
            return
        expert = self.expert.isChecked()
        if any(not macro_allowed(command, expert) for command in commands):
            self._error("Dieses Makro enthält erweiterte Befehle. Expert-Mode ist erforderlich.")
            return
        if expert and not self._confirm("Makro ausführen?", "Die eingegebenen CLI-Befehle werden auf dem Flipper ausgeführt."):
            return
        def work():
            for command in commands:
                if self.cancel_macro.is_set():
                    return "Makro abgebrochen"
                self._ensure_cli()
                self.client.send_command(command)
            return f"{len(commands)} Schritte abgeschlossen"
        self.submit("Makro ausführen", work, self._show_output)

    def _confirm(self, title, message):
        return QMessageBox.question(self, title, message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

    def _error(self, message):
        self.log.appendPlainText(f"[ERROR] {message}")
        self.statusBar().showMessage(message, 20000)

    def _clear_device(self):
        self.info.clear()
        self.dashboard.clear()
        self.device_label.setText("Kein Gerät")
        self.screen.clear()
        for browser in self.browsers:
            browser.clear()

    def _update_state(self):
        connected = self.connected
        self.connection_label.setText("Verbunden" if connected else "Nicht verbunden")
        self.ports.setEnabled(not connected and not self.busy)
        self.scan_button.setEnabled(not connected and not self.busy)
        self.connect_button.setEnabled(not connected and not self.busy)
        self.connect_button.setVisible(not connected)
        self._update_connection_identity()
        self.disconnect_button.setEnabled(connected)
        self.stop_button.setEnabled(connected and self.busy)
        self.stop_button.setVisible(self.busy)
        self.disconnect_button.setVisible(connected)
        self.live_button.setText("Live-Ansicht beenden" if self.rpc.is_connected else "Live-Ansicht starten")
        self.live_status.setText("Live über USB" if self.rpc.is_connected else "Live-Ansicht ist aus")
        self.progress.setVisible(self.busy)
        for control in self.device_controls:
            control.setEnabled(connected and not self.busy)
        self.dashboard.set_connection(connected, self.busy, self.rpc.is_connected)

    def _pump(self):
        for line in self.client.pop_logs():
            self.log.appendPlainText(line)
        frame = self.rpc.pop_frame()
        if frame:
            self.screen.set_frame(*frame)
        connected = self.connected
        if self.busy and not connected:
            return
        if self.was_connected and not connected:
            self._clear_device()
            if self.rpc.error:
                self._error("Display-Verbindung getrennt: " + self.rpc.error)
        if self.was_connected != connected:
            self._update_state()
        self.was_connected = connected

    def closeEvent(self, event):
        self.closing.set()
        self.disconnect_device()
        if self.jobs:
            self.statusBar().showMessage("Verbindung wird beendet …")
            event.ignore()
            return
        self.timer.stop()
        self.dashboard_timer.stop()
        event.accept()


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPixelSize(13)
    app.setFont(font)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("FlipperRemote")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
