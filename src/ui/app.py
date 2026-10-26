from __future__ import annotations

import posixpath
import shlex
import sys
import threading

from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QColor, QFontDatabase, QPalette, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDockWidget, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QFrame, QProgressBar, QStyle,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
    QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from core.connection_manager import scan_flipper_ports
from core.flipper_api import FlipperAPI
from core.serial_client import SerialClient
from core.rpc_display import RpcDisplay
from core.storage import quote_path
from persistence.config_store import ConfigStore
from ui.browser import FileBrowser
from ui.jobs import Job
from ui.screen import ScreenView
from ui.sidebar import Sidebar

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
        self.resize(1180, 820)
        self.setMinimumSize(960, 620)
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
        self._update_state()

    def _build(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 12)
        root_layout.setSpacing(16)
        top = QHBoxLayout()
        brand = QLabel("FLIPPER  /  CONTROL CENTER")
        brand.setObjectName("brand")
        top.addWidget(brand)
        top.addStretch()
        self.mode = QComboBox()
        self.mode.addItems(["Easy Mode", "Alle Werkzeuge"])
        self.mode.setAccessibleName("Bedienmodus")
        self.mode.setMinimumWidth(165)
        self.mode.setCurrentIndex(0 if self.settings.get("easy_mode", True) else 1)
        self.mode.currentIndexChanged.connect(self.change_mode)
        top.addWidget(self.mode)
        self.ports = QComboBox()
        self.ports.setAccessibleName("USB-Port")
        self.ports.setMinimumContentsLength(22)
        self.scan_button = QPushButton("Suchen")
        self.scan_button.clicked.connect(self.scan)
        self.connect_button = QPushButton("Verbinden")
        self.connect_button.clicked.connect(self.connect_device)
        self.disconnect_button = QPushButton("Trennen")
        self.disconnect_button.clicked.connect(self.disconnect_device)
        self.stop_button = QPushButton("Abbrechen")
        self.stop_button.setToolTip("Laufenden CLI-Befehl mit Strg+C abbrechen")
        self.stop_button.clicked.connect(self.interrupt)
        self.connection_label = QLabel("Nicht verbunden")
        for widget in [self.ports, self.scan_button, self.connect_button, self.disconnect_button, self.stop_button]:
            top.addWidget(widget)
        top.addStretch()
        top.addWidget(self.connection_label)
        root_layout.addLayout(top)
        splitter = QSplitter()
        self.nav = Sidebar()
        self.nav.addItems(MODULES)
        self.nav.setObjectName("sidebar")
        self.nav.setSpacing(4)
        icons = [QStyle.StandardPixmap.SP_ComputerIcon, QStyle.StandardPixmap.SP_FileDialogInfoView, QStyle.StandardPixmap.SP_DesktopIcon, QStyle.StandardPixmap.SP_DirIcon, QStyle.StandardPixmap.SP_MediaPlay, QStyle.StandardPixmap.SP_DriveFDIcon, QStyle.StandardPixmap.SP_BrowserReload, QStyle.StandardPixmap.SP_DriveHDIcon, QStyle.StandardPixmap.SP_FileDialogDetailedView, QStyle.StandardPixmap.SP_FileDialogContentsView]
        for index, icon in enumerate(icons):
            self.nav.item(index).setIcon(self.style().standardIcon(icon))
        self.nav.setAccessibleName("Module")
        self.nav.setMinimumWidth(145)
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
        splitter.addWidget(self.nav)
        splitter.addWidget(self.stack)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([160, 900])
        root_layout.addWidget(splitter)
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
        label = QLabel(title)
        font = label.font()
        font.setPointSize(font.pointSize() + 7)
        font.setBold(True)
        label.setFont(font)
        label.setObjectName("pageTitle")
        layout.addWidget(label)
        hint = QLabel(subtitle)
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        layout.setContentsMargins(26, 12, 14, 12)
        layout.setSpacing(16)
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
        page, layout = self._page("Was möchtest du machen?", "Dein Computer ist die Oberfläche. Dein Flipper übernimmt die Hardware.")
        hero = QFrame()
        hero.setObjectName("deviceCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        heading = QLabel("Dein Flipper")
        heading.setObjectName("cardTitle")
        self.home_device = QLabel(self.device_description)
        self.home_device.setWordWrap(True)
        hero_layout.addWidget(heading)
        hero_layout.addWidget(self.home_device)
        layout.addWidget(hero)
        cards = QGridLayout()
        cards.setSpacing(14)
        tasks = [
            ("Flipper bedienen", "Live-Display und Tasten. Die Gerätefunktionen direkt vom Desktop aus bedienen.", "Remote", QStyle.StandardPixmap.SP_DesktopIcon),
            ("Fernbedienungen", "Gespeicherte Infrarot-Fernbedienungen finden und auf dem Flipper öffnen.", "Infrared", QStyle.StandardPixmap.SP_MediaPlay),
            ("Dateien verwalten", "SD-Karte durchsuchen, Dateien ansehen und Ordner verwalten.", "Storage", QStyle.StandardPixmap.SP_DirIcon),
            ("Karten & Tags", "Gespeicherte NFC-Dateien ansehen und für die Geräte-App auswählen.", "NFC/RFID", QStyle.StandardPixmap.SP_DriveFDIcon),
            ("Funk-Signale", "Sub-GHz-Dateien durchsuchen und die Geräte-App bedienen.", "Sub-GHz", QStyle.StandardPixmap.SP_BrowserReload),
            ("USB-Abläufe", "Gespeicherte Skripte ansehen. Ausführen bleibt eine bewusste Aktion.", "BadUSB", QStyle.StandardPixmap.SP_DriveHDIcon),
        ]
        for index, (title, description, module, icon) in enumerate(tasks):
            card = QFrame()
            card.setObjectName("taskCard")
            inner = QVBoxLayout(card)
            inner.setContentsMargins(18, 16, 18, 16)
            button = QPushButton(title)
            button.setIcon(self.style().standardIcon(icon))
            button.setObjectName("taskAction")
            button.clicked.connect(lambda checked=False, name=module: self.nav.setCurrentRow(MODULES.index(name)))
            text = QLabel(description)
            text.setWordWrap(True)
            text.setObjectName("subtitle")
            inner.addWidget(button)
            inner.addWidget(text)
            cards.addWidget(card, index // 2, index % 2)
        layout.addLayout(cards)
        layout.addStretch()
        return page

    def change_mode(self, index):
        self.settings["easy_mode"] = index == 0
        self._save(self.store.save_settings, self.settings)
        self._apply_mode()

    def _apply_mode(self):
        easy = self.settings.get("easy_mode", True)
        for index, name in enumerate(MODULES):
            self.nav.item(index).setHidden(easy and name in {"System", "Makros"})
        easy_names = {"Remote": "Flipper bedienen", "Storage": "Dateien", "Infrared": "Fernbedienungen", "NFC/RFID": "Karten & Tags", "Sub-GHz": "Funk-Signale", "BadUSB": "USB-Abläufe"}
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
        body = QHBoxLayout()
        body.setSpacing(22)
        display = QVBoxLayout()
        self.screen = ScreenView()
        display.addWidget(self.screen, 1)
        live_row = QHBoxLayout()
        self.live_button = QPushButton("Live-Ansicht starten")
        self.live_button.clicked.connect(self.toggle_live)
        self.device_controls.append(self.live_button)
        live_row.addWidget(self.live_button)
        self.live_status = QLabel("Display noch nicht verbunden")
        live_row.addWidget(self.live_status)
        live_row.addStretch()
        display.addLayout(live_row)
        body.addLayout(display, 3)
        controls = QVBoxLayout()
        group = QGroupBox("Navigation")
        grid = QGridLayout(group)
        for label, key, row, column in [("↑", "up", 0, 1), ("←", "left", 1, 0), ("OK", "ok", 1, 1), ("→", "right", 1, 2), ("↓", "down", 2, 1), ("Zurück", "back", 3, 1)]:
            button = QPushButton(label)
            button.setAccessibleName({"up": "Nach oben", "down": "Nach unten", "left": "Nach links", "right": "Nach rechts", "ok": "OK", "back": "Zurück"}[key])
            button.setMinimumSize(64, 42)
            button.clicked.connect(lambda checked=False, k=key: self.send_key(k))
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
        layout.addLayout(body, 1)
        for shortcut, key in [("Up", "up"), ("Down", "down"), ("Left", "left"), ("Right", "right"), ("Return", "ok"), ("Backspace", "back"), ("Escape", "back")]:
            binding = QShortcut(QKeySequence(shortcut), page)
            binding.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            binding.setAutoRepeat(False)
            binding.activated.connect(lambda k=key: self.send_key(k))
        return page

    def _browser_page(self, title, root, suffix=None, app_name=None):
        subtitle = "Echte Dateien vom Gerät. Ordner doppelklicken, um hineinzuwechseln."
        if app_name:
            subtitle += " Öffnen startet die Geräte-App; Bedienung über Remote. Expert-Mode erforderlich."
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
        self.macro_select = QComboBox()
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
        self.theme = QComboBox()
        self.theme.addItems(["System", "Hell", "Dunkel"])
        self.theme.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(self.settings.get("theme"), 0))
        self.theme.currentIndexChanged.connect(self.save_preferences)
        form.addRow("Darstellung", self.theme)
        self.start_module = QComboBox()
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
        if 3 <= index <= 7 and self.connected and not self.busy:
            browser = self.browsers[index - 3]
            self.browse(browser, browser.current_path)

    def _apply_settings(self):
        mode = self.settings.get("theme", "system")
        palette = QPalette(self._system_palette)
        if mode == "dark":
            for role, color in [(QPalette.ColorRole.Window, "#252525"), (QPalette.ColorRole.WindowText, "#eeeeee"), (QPalette.ColorRole.Base, "#191919"), (QPalette.ColorRole.AlternateBase, "#303030"), (QPalette.ColorRole.Text, "#eeeeee"), (QPalette.ColorRole.Button, "#303030"), (QPalette.ColorRole.ButtonText, "#eeeeee"), (QPalette.ColorRole.Highlight, "#ae5800"), (QPalette.ColorRole.HighlightedText, "#ffffff")]:
                palette.setColor(role, QColor(color))
        elif mode == "light":
            for role, color in [(QPalette.ColorRole.Window, "#f3f3f3"), (QPalette.ColorRole.WindowText, "#202020"), (QPalette.ColorRole.Base, "#ffffff"), (QPalette.ColorRole.AlternateBase, "#eeeeee"), (QPalette.ColorRole.Text, "#202020"), (QPalette.ColorRole.Button, "#eeeeee"), (QPalette.ColorRole.ButtonText, "#202020"), (QPalette.ColorRole.Highlight, "#b65b00"), (QPalette.ColorRole.HighlightedText, "#ffffff")]:
                palette.setColor(role, QColor(color))
        QApplication.setPalette(palette)
        dark = palette.color(QPalette.ColorRole.Window).lightness() < 128
        border = "#3c4149" if dark else "#dce0e5"
        card = "#292d33" if dark else "#ffffff"
        muted = "#adb4c0" if dark else "#626b79"
        selected = "#623c20" if dark else "#fff0df"
        self.setStyleSheet(f"""
            QMainWindow {{ background: palette(window); }}
            QLabel#brand {{ font-size: 11px; font-weight: 700; letter-spacing: 1px; color: {muted}; }}
            QLabel#pageTitle {{ font-size: 26px; font-weight: 700; }}
            QLabel#subtitle {{ color: {muted}; line-height: 1.4; }}
            QLabel#cardTitle {{ font-size: 18px; font-weight: 600; }}
            QFrame#deviceCard, QFrame#taskCard {{ background: {card}; border: 1px solid {border}; border-radius: 12px; }}
            QWidget#sidebar {{ background: transparent; }}
            QWidget#sidebar QPushButton {{ text-align: left; border: none; padding: 10px 12px; border-radius: 7px; background: transparent; }}
            QWidget#sidebar QPushButton:checked {{ background: {selected}; color: #e88730; font-weight: 600; }}
            QPushButton {{ padding: 7px 13px; }}
            QPushButton#taskAction {{ text-align: left; font-size: 16px; font-weight: 600; padding: 5px 0; border: none; background: transparent; }}
            QPushButton#taskAction:hover {{ color: #df7b22; }}
            QComboBox {{ padding: 5px 9px; }}
            QTreeWidget {{ border: 1px solid {border}; border-radius: 7px; }}
            QPlainTextEdit {{ border: 1px solid {border}; border-radius: 7px; padding: 6px; }}
            QStatusBar {{ color: {muted}; }}
        """)
        for browser in self.browsers:
            browser.expert = self.settings.get("expert_mode") is True
            browser.update_actions()

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
        return self.submit(command, work, success)

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
                    return ""
                return self.client.send_command("device_info")
            except Exception:
                self.client.disconnect()
                raise
        def connected(info):
            self.connected_port = port
            self.settings["last_port"] = port
            self._save(self.store.save_settings, self.settings)
            self._show_info(info)
        self.submit("Flipper verbinden", work, connected, require_connection=False)

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
        self.device_description = " · ".join(filter(None, [values.get("hardware_name"), values.get("firmware_origin_fork"), values.get("firmware_version"), "USB verbunden"]))
        self.home_device.setText(self.device_description)

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
        self.home_device.setText("Flipper anschließen und verbinden")
        self.screen.clear()
        for browser in self.browsers:
            browser.clear()

    def _update_state(self):
        connected = self.connected
        self.connection_label.setText("Verbunden" if connected else "Nicht verbunden")
        self.ports.setEnabled(not connected and not self.busy)
        self.scan_button.setEnabled(not connected and not self.busy)
        self.connect_button.setEnabled(not connected and not self.busy)
        self.disconnect_button.setEnabled(connected)
        self.stop_button.setEnabled(connected and self.busy)
        self.stop_button.setVisible(self.busy)
        self.disconnect_button.setVisible(connected)
        self.live_button.setText("Live-Ansicht beenden" if self.rpc.is_connected else "Live-Ansicht starten")
        self.live_status.setText("Live über USB" if self.rpc.is_connected else "Live-Ansicht ist aus")
        self.progress.setVisible(self.busy)
        for control in self.device_controls:
            control.setEnabled(connected and not self.busy)

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
        event.accept()


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("FlipperRemote")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
