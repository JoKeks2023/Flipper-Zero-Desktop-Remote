"""Small local IPC client, independent of Qt and the optional MCP SDK."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import stat

MAX_REQUEST = 8192
MAX_RESPONSE = 1_048_576


def default_socket_path():
    # MCP hosts sanitize TMPDIR/XDG variables; both processes need a stable path.
    return Path("/tmp") / f"flipper-remote-{os.getuid()}" / "bridge.sock"


class BridgeClient:
    def __init__(self, path=None, timeout=20):
        self.path = Path(path) if path else default_socket_path()
        self.timeout = timeout

    def call(self, operation, **arguments):
        request = json.dumps({"operation": operation, "arguments": arguments}, ensure_ascii=False).encode() + b"\n"
        if len(request) > MAX_REQUEST:
            raise ValueError("Anfrage zu groß")
        try:
            parent, endpoint = self.path.parent.lstat(), self.path.lstat()
            if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                    or parent.st_mode & 0o077 or not stat.S_ISSOCK(endpoint.st_mode)
                    or endpoint.st_uid != os.getuid()):
                raise RuntimeError("Ungültige lokale MCP-Verbindung")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(self.timeout)
                connection.connect(str(self.path))
                connection.sendall(request)
                response = bytearray()
                while b"\n" not in response:
                    chunk = connection.recv(65536)
                    if not chunk:
                        raise RuntimeError("Desktop-Verbindung beendet; Aktion nicht automatisch wiederholen")
                    response.extend(chunk)
                    if len(response) > MAX_RESPONSE:
                        raise RuntimeError("Antwort zu groß")
        except (FileNotFoundError, ConnectionRefusedError):
            raise RuntimeError("Desktop-App öffnen und unter Einstellungen den MCP-Zugriff aktivieren") from None
        except TimeoutError:
            raise RuntimeError("Desktop-Anfrage hat zu lange gedauert; Ergebnis vor erneutem Ausführen prüfen") from None
        result = json.loads(response.split(b"\n", 1)[0])
        if "error" in result:
            raise RuntimeError(result["error"])
        return result["result"]
