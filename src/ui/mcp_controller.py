"""MCP calls use the same serial owner, permissions and job queue as the UI."""
import base64
from dataclasses import asdict
from datetime import datetime
import posixpath

from PySide6.QtCore import QBuffer, QIODevice

from core.device_status import read_device_status
from core.flipper_api import FlipperAPI
from core.storage import quote_path

OPERATIONS = {
    "status": {"refresh"}, "list_directory": {"path"}, "read_text": {"path"},
    "get_screen": set(), "set_live_view": {"enabled"}, "press_key": {"key", "long"},
}
CONTROL = {"set_live_view", "press_key"}
TEXT_SUFFIXES = {".txt", ".ir", ".nfc", ".rfid", ".sub", ".ibtn", ".js", ".json",
                 ".csv", ".md", ".conf", ".log", ".ini", ".fuf"}


class MCPController:
    def __init__(self, window):
        self.window = window

    def _check_access(self, operation):
        settings = self.window.settings
        if not settings.get("mcp_enabled") or self.window.closing.is_set():
            raise RuntimeError("MCP-Zugriff ist in der Desktop-App ausgeschaltet")
        if operation in CONTROL and not settings.get("mcp_control"):
            raise RuntimeError("Bedienung nicht freigegeben. In der App 'Lesen & Bedienen' wählen")

    def _status(self):
        w = self.window
        status = asdict(w.dashboard.status)
        stamp = status.pop("received_at")
        return {"connected": w.connected, "live_view": w.rpc.is_connected, "busy": w.busy,
                "permission": "control" if w.settings.get("mcp_control") else "read_only",
                "measured_at": stamp.isoformat() if stamp else None,
                "age_seconds": (datetime.now().astimezone() - stamp).total_seconds() if stamp else None,
                "units": {"power": {"voltage": "mV", "current": "mA", "capacity": "mAh", "temperature": "°C", "charge_health": "%"} if status["power"].get("format.major") == "2" else {},
                          "debug": {"charger.vbus": "mV", "charger.vsys": "mV", "charger.vbat": "mV", "charger.vreg": "mV", "charger.current": "mA"} if status["debug"].get("format.major") == "1" else {}},
                **status}

    @staticmethod
    def _path(arguments):
        path = arguments.get("path", "/ext")
        if not isinstance(path, str) or len(path) > 1024 or ".." in path.split("/"):
            raise ValueError("Ungültiger Gerätepfad")
        quote_path(path)
        return posixpath.normpath(path)

    @staticmethod
    def _boolean(arguments, key, default=False):
        value = arguments.get(key, default)
        if type(value) is not bool:
            raise ValueError(f"{key} muss ein Wahrheitswert sein")
        return value

    def dispatch(self, operation, arguments, reply):
        w = self.window
        if not isinstance(operation, str) or operation not in OPERATIONS:
            reply(error="Unbekannte MCP-Aktion")
            return
        def respond(result=None, error=None):
            w.mcp_panel.activity(operation, error)
            reply(result=result, error=error)
        try:
            self._check_access(operation)
            if set(arguments) - OPERATIONS[operation]:
                raise ValueError("Unbekannte Argumente")
            if operation == "status" and not self._boolean(arguments, "refresh"):
                respond(self._status())
                return
            if not w.connected:
                raise RuntimeError("Flipper zuerst in der Desktop-App verbinden")
            if operation == "get_screen":
                if not w.rpc.is_connected or w.screen.image is None or not w.frame_time:
                    raise RuntimeError("Noch kein Live-Bild. Live-Ansicht in der App starten")
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                if not w.screen.image.save(buffer, "PNG"):
                    raise RuntimeError("Display-Bild konnte nicht erstellt werden")
                respond({"image": base64.b64encode(bytes(buffer.data())).decode("ascii"),
                         "captured_at": w.frame_time.isoformat(),
                         "age_seconds": (datetime.now().astimezone() - w.frame_time).total_seconds()})
                return
            if w.busy:
                raise RuntimeError("Flipper ist beschäftigt. Aktuelle Aktion zuerst abschließen lassen")
            if operation in {"status", "list_directory", "read_text"} and w.rpc.is_connected:
                raise RuntimeError("Für diese Abfrage die Live-Ansicht in der Desktop-App beenden")
            path = self._path(arguments) if operation in {"list_directory", "read_text"} else None
            enabled = self._boolean(arguments, "enabled") if operation == "set_live_view" else None
            long_press = self._boolean(arguments, "long") if operation == "press_key" else None
            key = arguments.get("key")
            if operation == "press_key" and key not in {"up", "down", "left", "right", "ok", "back"}:
                raise ValueError("Unbekannte Taste")
            if operation == "read_text" and posixpath.splitext(path)[1].lower() not in TEXT_SUFFIXES:
                raise ValueError("Vorschau nur für unterstützte Textdateien, z. B. .ir, .nfc, .sub oder .txt")

            def work():
                self._check_access(operation)
                def send(command, **kwargs):
                    self._check_access(operation)
                    if w.cancel_macro.is_set():
                        raise InterruptedError("MCP-Aktion abgebrochen")
                    return w.client.send_command(command, **kwargs)
                api = FlipperAPI(send)
                if operation == "status":
                    return read_device_status(send, w.cancel_macro.is_set)
                if operation == "list_directory":
                    return {"path": path, "entries": [asdict(e) for e in api.list_directory(path)]}
                if operation == "read_text":
                    entry = next((e for e in api.list_directory(posixpath.dirname(path)) if e.path == path), None)
                    if not entry or entry.is_dir or entry.size is None:
                        raise ValueError("Keine lesbare Datei mit bekannter Größe gefunden")
                    if entry.size > 128_000:
                        raise ValueError("Textvorschau auf 128 KB begrenzt")
                    text = send(f"storage read {quote_path(path)}")
                    header, separator, body = text.partition("\n")
                    if separator and header.strip() == f"Size: {entry.size}":
                        text = body
                    if len(text.encode("utf-8")) > 128_000:
                        raise ValueError("Datei während des Lesens zu groß geworden")
                    return {"path": path, "size": entry.size, "text": text, "normalized_preview": True, "untrusted_content": True}
                if operation == "press_key":
                    if w.rpc.is_connected:
                        w.rpc.input(key, long_press)
                    else:
                        send(f"input send {key} {'long' if long_press else 'short'}")
                    return {"sent": True, "key": key, "long": long_press}
                if operation == "set_live_view":
                    if enabled and not w.rpc.is_connected:
                        w.client.disconnect()
                        try:
                            w.rpc.connect(w.connected_port)
                            if w.cancel_macro.is_set() or w.closing.is_set():
                                w.rpc.disconnect(graceful=False)
                                raise InterruptedError("Live-Ansicht abgebrochen")
                        except Exception:
                            if not w.closing.is_set() and not w.cancel_macro.is_set():
                                w.client.connect(w.connected_port)
                            raise
                    elif not enabled and w.rpc.is_connected:
                        w._ensure_cli()
                    return {"live_view": w.rpc.is_connected}

            def success(result):
                if operation == "status":
                    w._show_status(result)
                    result = self._status()
                elif operation == "set_live_view" and not enabled:
                    w.screen.clear()
                    w.frame_time = None
                respond(result)
            if not w.submit("MCP · " + operation, work, success,
                            failure=lambda error: respond(error=error)):
                respond(error="Desktop-App ist beschäftigt")
        except Exception as exc:
            respond(error=exc)
