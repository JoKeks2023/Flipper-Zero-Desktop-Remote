"""Compact, real device status. Technical raw values are available on demand."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from core.device_status import DeviceStatus, measurement


def label(text, role="subtitle"):
    widget = QLabel(text)
    widget.setObjectName(role)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


class DeviceDashboard(QWidget):
    refresh_requested = Signal()
    remote_requested = Signal()

    def __init__(self):
        super().__init__()
        self.status = DeviceStatus()
        self.online = False
        self.paused = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        identity = QHBoxLayout()
        names = QVBoxLayout()
        names.setSpacing(3)
        self.name = label("Flipper Zero", "deviceHeading")
        self.connection = label("Per USB verbinden, um den Gerätestatus zu sehen.")
        names.addWidget(self.name)
        names.addWidget(self.connection)
        identity.addLayout(names, 1)
        self.refresh = QPushButton("Aktualisieren")
        self.refresh.setAccessibleName("Dashboard aktualisieren")
        self.refresh.clicked.connect(self.refresh_requested)
        identity.addWidget(self.refresh)
        launch = QPushButton("Flipper bedienen")
        launch.setProperty("role", "primary")
        launch.clicked.connect(self.remote_requested)
        identity.addWidget(launch)
        layout.addLayout(identity)

        metrics = QFrame()
        metrics.setObjectName("dashboardMetrics")
        metric_layout = QHBoxLayout(metrics)
        metric_layout.setContentsMargins(16, 12, 16, 12)
        metric_layout.setSpacing(20)
        self.metrics, self.notes = {}, {}
        for index, (key, title) in enumerate((("battery", "Akkustand"),
                                               ("usb", "USB-Spannung"),
                                               ("temperature", "Akku-Temperatur"))):
            if index:
                divider = QFrame()
                divider.setObjectName("dashboardDivider")
                divider.setFixedWidth(1)
                metric_layout.addWidget(divider)
            column = QVBoxLayout()
            column.setSpacing(6)
            column.addWidget(label(title, "metricLabel"))
            self.metrics[key] = label("—", "metricValue")
            self.metrics[key].setAccessibleDescription(title)
            column.addWidget(self.metrics[key])
            self.notes[key] = label("Nicht verbunden", "metricNote")
            column.addWidget(self.notes[key])
            if key == "battery":
                self.battery_bar = QProgressBar()
                self.battery_bar.setObjectName("batteryLevel")
                self.battery_bar.setRange(0, 100)
                self.battery_bar.setTextVisible(False)
                self.battery_bar.setFixedHeight(4)
                self.battery_bar.setAccessibleName("Akkustand in Prozent")
                column.addWidget(self.battery_bar)
            else:
                column.addSpacing(4)
            metric_layout.addLayout(column, 1)
        layout.addWidget(metrics)

        details = QHBoxLayout()
        details.setSpacing(32)
        self.values = {}
        groups = (
            ("Akku & Strom", (("voltage", "Akku-Spannung"), ("current", "Akku-Strom"),
                              ("remaining", "Restkapazität"), ("full", "Volle Kapazität"),
                              ("design", "Auslegungskapazität"), ("limit", "Ladeschlussspannung"))),
            ("Gerät & Firmware", (("firmware", "Firmware"), ("built", "Erstellt am"),
                                 ("hardware", "Hardware"), ("region", "Region"),
                                 ("system_voltage", "Systemspannung"), ("protocol", "Protokoll"))),
        )
        for heading, rows in groups:
            column = QVBoxLayout()
            column.setSpacing(7)
            column.addWidget(label(heading, "cardTitle"))
            grid = QGridLayout()
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(6)
            for row, (key, title) in enumerate(rows):
                grid.addWidget(label(title), row, 0)
                value = label("—", "detailValue")
                value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value.setAccessibleDescription(title)
                grid.addWidget(value, row, 1)
                self.values[key] = value
            grid.setColumnStretch(1, 1)
            column.addLayout(grid)
            details.addLayout(column, 1)
        layout.addLayout(details)
        footer = QHBoxLayout()
        self.freshness = label("Noch keine Messwerte", "caption")
        self.freshness.setWordWrap(True)
        footer.addWidget(self.freshness, 1)
        self.all_details = QPushButton("Alle Geräteinfos…")
        self.all_details.setProperty("role", "ghost")
        self.all_details.clicked.connect(self.show_details)
        footer.addWidget(self.all_details)
        layout.addLayout(footer)
        self.clear()

    def show_status(self, status):
        self.status = status
        device = status.device
        self.name.setText(device.get("hardware_name") or device.get("hardware_model") or "Flipper Zero")
        self.connection.setText(" · ".join(filter(None, (device.get("hardware_model", "Flipper Zero"), "USB verbunden"))))
        self.metrics["battery"].setText(measurement(status.charge_level, "%"))
        self.notes["battery"].setText(status.charge_state)
        self.battery_bar.setValue(round(status.charge_level or 0))
        self.battery_bar.setVisible(status.charge_level is not None)
        vbus = status.number("charger.vbus", debug=True, minimum=0)
        self.metrics["usb"].setText(measurement(vbus / 1000 if vbus is not None else None, "V", 2))
        self.notes["usb"].setText("Gemessen am USB-Eingang" if vbus is not None else "Nicht verfügbar")
        self.metrics["temperature"].setText(measurement(status.number("battery.temp"), "°C"))
        health = status.number("battery.health", minimum=0, maximum=100)
        self.notes["temperature"].setText("Gesundheit " + measurement(health, "%") if health is not None else "Gesundheit nicht verfügbar")
        for key, source, unit, divisor, decimals, debug in (
            ("voltage", "battery.voltage", "V", 1000, 3, False),
            ("current", "battery.current", "mA", 1, 0, False),
            ("remaining", "capacity.remain", "mAh", 1, 0, False),
            ("full", "capacity.full", "mAh", 1, 0, False),
            ("design", "capacity.design", "mAh", 1, 0, False),
            ("limit", "charge.voltage.limit", "V", 1000, 3, False),
            ("system_voltage", "charger.vsys", "V", 1000, 3, True),
        ):
            number = status.number(source, debug=debug, minimum=None if key == "current" else 0)
            self.values[key].setText(measurement(number / divisor if number is not None else None, unit, decimals))
        self.values["current"].setToolTip("Vom Akku-Messchip gemeldeter Strom, einschließlich Vorzeichen.")
        firmware = " · ".join(filter(None, (device.get("firmware_origin_fork"), device.get("firmware_version"))))
        self.values["firmware"].setText(firmware or "—")
        self.values["built"].setText(device.get("firmware_build_date") or "—")
        self.values["hardware"].setText(" · ".join(filter(None, (
            "Rev. " + device["hardware_ver"] if device.get("hardware_ver") else None,
            "F" + device["hardware_target"] if device.get("hardware_target") else None))) or "—")
        self.values["region"].setText(device.get("hardware_region_provisioned") or device.get("hardware_region") or "—")
        version = [device.get("protobuf_version_major"), device.get("protobuf_version_minor")]
        self.values["protocol"].setText("RPC " + ".".join(version) if all(version) else "—")
        self._update_freshness()

    def set_connection(self, online, busy=False, paused=False):
        self.online, self.paused = online, paused
        self.refresh.setEnabled(online and not busy and not paused)
        self.refresh.setToolTip("Für neue Messwerte zuerst die Live-Ansicht beenden." if paused else "Messwerte vom Flipper neu laden")
        self.all_details.setEnabled(online and bool(self.status.device or self.status.power or self.status.debug))
        self._update_freshness()

    def _update_freshness(self):
        stamp = self.status.received_at.strftime("%H:%M:%S") if self.status.received_at else None
        if not self.online:
            text = "Flipper anschließen und verbinden"
        elif self.paused:
            text = "Aktualisierung pausiert · Live-Ansicht aktiv"
            if stamp:
                text += " · Letzte Messung " + stamp
        elif self.status.errors:
            names = {"device": "Geräteinfo", "power": "Akku", "debug": "Power-Diagnose"}
            text = " · ".join(names[source] + " nicht verfügbar" for source in self.status.errors)
            if stamp:
                text += " · Abgefragt " + stamp
        elif stamp:
            text = "Aktualisiert " + stamp + " · Automatisch alle 10 s auf dieser Seite"
        else:
            text = "Messwerte werden geladen …"
        self.freshness.setText(text)
        self.freshness.setToolTip("\n".join(f"{key}: {value}" for key, value in self.status.errors.items()))

    def clear(self):
        self.show_status(DeviceStatus())
        self.name.setText("Flipper Zero")
        self.connection.setText("Per USB verbinden, um den Gerätestatus zu sehen.")
        for note in self.notes.values():
            note.setText("Nicht verbunden")
        self.set_connection(False)

    def show_details(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Alle Geräteinformationen")
        dialog.resize(660, 480)
        layout = QVBoxLayout(dialog)
        stamp = self.status.received_at.strftime("%H:%M:%S") if self.status.received_at else "—"
        layout.addWidget(label("Momentaufnahme vom Flipper · " + stamp))
        tabs = QTabWidget()
        for title, source in (("Gerät", "device"), ("Akku & Strom", "power"), ("Power-Diagnose", "debug")):
            tree = QTreeWidget()
            tree.setHeaderLabels(["Eigenschaft", "Rohwert"])
            tree.setRootIsDecorated(False)
            tree.setColumnWidth(0, 300)
            for key, value in getattr(self.status, source).items():
                tree.addTopLevelItem(QTreeWidgetItem([key, value]))
            if source in self.status.errors:
                tree.addTopLevelItem(QTreeWidgetItem(["Nicht verfügbar", self.status.errors[source]]))
            tabs.addTab(tree, title)
        layout.addWidget(tabs, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Schließen")
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
