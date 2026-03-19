from __future__ import annotations

import queue
import threading
from typing import List, Optional

import serial


class SerialClient:
    def __init__(self) -> None:
        self._serial: Optional[serial.Serial] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue()

    @property
    def is_connected(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def connect(self, port: str, baudrate: int = 115200) -> None:
        self.disconnect()
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=0.1)
        self._stop_event.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        self._log_queue.put(f"[INFO] Connected to {port} @ {baudrate} baud")

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.6)
        self._reader_thread = None

        if self._serial:
            try:
                port = self._serial.port
            except Exception:
                port = "unknown"
            try:
                self._serial.close()
                self._log_queue.put(f"[INFO] Disconnected from {port}")
            except Exception as exc:
                self._log_queue.put(f"[WARN] Disconnect error: {exc}")
            finally:
                self._serial = None

    def send_command(self, command: str) -> None:
        if not self.is_connected:
            raise RuntimeError("Not connected to Flipper")
        payload = (command.strip() + "\r\n").encode("utf-8")
        self._serial.write(payload)
        self._log_queue.put(f"> {command.strip()}")

    def pop_logs(self, max_lines: int = 200) -> List[str]:
        lines: list[str] = []
        while len(lines) < max_lines:
            try:
                lines.append(self._log_queue.get_nowait())
            except queue.Empty:
                break
        return lines

    def _reader_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self._serial or not self._serial.is_open:
                    break
                line = self._serial.readline()
                if not line:
                    continue
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    self._log_queue.put(decoded)
            except Exception as exc:
                self._log_queue.put(f"[ERROR] Serial read error: {exc}")
                break
