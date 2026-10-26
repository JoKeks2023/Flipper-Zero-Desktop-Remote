"""User-private Unix socket. Device work is dispatched through Qt's existing worker."""
import json
import os
from pathlib import Path
import stat

from PySide6.QtCore import QObject, QLockFile, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from flipper_mcp.bridge_client import MAX_REQUEST, MAX_RESPONSE, default_socket_path


class LocalBridge(QObject):
    def __init__(self, dispatch, parent=None, path=None):
        super().__init__(parent)
        self.path = Path(path) if path else default_socket_path()
        self.dispatch = dispatch
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.setMaxPendingConnections(8)
        self.server.newConnection.connect(self._accept)
        self.lock = None
        self.clients = set()

    @property
    def running(self):
        return self.server.isListening()

    def start(self):
        if self.running:
            return
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory = self.path.parent.lstat()
        if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid() or directory.st_mode & 0o077:
            raise RuntimeError("MCP-Verzeichnis muss privat sein und diesem Benutzer gehören")
        self.lock = QLockFile(str(self.path.parent / "owner.lock"))
        self.lock.setStaleLockTime(0)
        if not self.lock.tryLock(0):
            self.lock = None
            raise RuntimeError("Eine andere Flipper-App stellt MCP bereits bereit")
        try:
            if self.path.exists():
                if not stat.S_ISSOCK(self.path.lstat().st_mode):
                    raise RuntimeError("Ungültige MCP-Socket-Datei")
                QLocalServer.removeServer(str(self.path))
            if not self.server.listen(str(self.path)):
                raise RuntimeError(self.server.errorString())
        except Exception:
            self.lock.unlock()
            self.lock = None
            raise

    def stop(self):
        self.server.close()
        for client in list(self.clients):
            client.abort()
        if self.lock:
            self.lock.unlock()
            self.lock = None

    def _accept(self):
        while self.server.hasPendingConnections():
            client = self.server.nextPendingConnection()
            if len(self.clients) >= 8:
                client.abort()
                client.deleteLater()
                continue
            self.clients.add(client)
            client.setReadBufferSize(MAX_REQUEST + 1)
            buffer = bytearray()
            timer = QTimer(client)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda c=client: c.abort() if c in self.clients else None)
            timer.start(20_000)
            state = {"handled": False}

            def reply(result=None, error=None, c=client):
                if c not in self.clients or c.state() != QLocalSocket.LocalSocketState.ConnectedState:
                    return
                payload = json.dumps({"error": str(error)} if error else {"result": result}, ensure_ascii=False).encode() + b"\n"
                if len(payload) > MAX_RESPONSE:
                    payload = b'{"error":"Antwort zu gross"}\n'
                c.write(payload)
                c.disconnectFromServer()

            def ready(c=client, data=buffer, seen=state, respond=reply):
                if seen["handled"]:
                    return
                data.extend(bytes(c.readAll()))
                if len(data) > MAX_REQUEST:
                    seen["handled"] = True
                    respond(error="Anfrage zu groß")
                elif b"\n" in data:
                    seen["handled"] = True
                    try:
                        request = json.loads(data.split(b"\n", 1)[0])
                        if not isinstance(request, dict) or not isinstance(request.get("arguments", {}), dict):
                            raise ValueError("Ungültige Anfrage")
                        self.dispatch(request.get("operation"), request.get("arguments", {}), respond)
                    except Exception as exc:
                        respond(error=str(exc))

            def closed(c=client):
                self.clients.discard(c)
                c.deleteLater()
            client.readyRead.connect(ready)
            client.disconnected.connect(closed)
            ready()
