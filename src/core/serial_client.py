from __future__ import annotations

import codecs
import queue
import re
import threading
import time
from typing import Optional

import serial


ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
PROMPT = re.compile(r"(?:^|\n)>: ?$")
CLI_ERROR = re.compile(
    r"(?im)^(?:Storage error:|Error:|Unknown command|Command not found|"
    r"Invalid (?:command|arguments)|Usage:|.*: command not found)"
)


class SerialClient:
    """One reader, one serialized CLI transaction, completed by the device prompt."""

    def __init__(self) -> None:
        self._serial: Optional[serial.Serial] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue(maxsize=2000)
        self._condition = threading.Condition()
        self._command_lock = threading.Lock()
        self._prompt_count = 0
        self._response = ""
        self._error: str | None = None

    def _log(self, line: str) -> None:
        try:
            self._log_queue.put_nowait(line)
        except queue.Full:
            try:
                self._log_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._log_queue.put_nowait(line)
            except queue.Full:
                pass

    @property
    def is_connected(self) -> bool:
        with self._condition:
            return bool(self._serial and self._serial.is_open and not self._error)

    def connect(self, port: str, baudrate: int = 115200) -> None:
        self.disconnect()
        connection = serial.Serial(port=port, baudrate=baudrate, timeout=0.1, write_timeout=2)
        with self._condition:
            self._serial = connection
            self._prompt_count = 0
            self._response = ""
            self._error = None
        stop = threading.Event()
        self._stop_event = stop
        self._reader_thread = threading.Thread(target=self._reader_loop, args=(connection, stop), daemon=True)
        self._reader_thread.start()
        try:
            # Opening USB CLI produces a welcome banner and a prompt, without a command.
            self._wait_for_prompt(connection, 0, 5)
        except Exception:
            self.disconnect()
            raise
        self._log(f"[INFO] Connected to {port} @ {baudrate} baud")

    def disconnect(self) -> None:
        self._stop_event.set()
        with self._condition:
            connection = self._serial
            self._serial = None
            self._condition.notify_all()
        thread = self._reader_thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1)
        if connection:
            connection.close()
            self._log(f"[INFO] Disconnected from {connection.port}")
        self._reader_thread = None

    def _wait_for_prompt(self, connection, previous: int, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        with self._condition:
            while self._prompt_count <= previous:
                if self._serial is not connection or self._error:
                    raise RuntimeError(self._error or "Connection closed")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Flipper CLI did not return its prompt")
                self._condition.wait(remaining)
            if self._serial is not connection or self._error:
                raise RuntimeError(self._error or "Connection closed")
            return self._response

    def send_command(self, command: str, timeout: float = 10) -> str:
        clean = command.strip()
        if not clean or any(ord(char) < 32 or ord(char) == 127 for char in clean):
            raise ValueError("Expected one non-empty CLI command without control characters")
        with self._command_lock:
            with self._condition:
                if not self.is_connected:
                    raise RuntimeError("Not connected to Flipper")
                connection = self._serial
                previous = self._prompt_count
                self._response = ""
            self._log(f"> {clean}")
            try:
                connection.write((clean + "\r").encode("utf-8"))
                response = self._wait_for_prompt(connection, previous, timeout)
            except TimeoutError:
                # Stop an interactive command before allowing the next transaction.
                try:
                    connection.write(b"\x03")
                    self._wait_for_prompt(connection, previous, 2)
                except Exception:
                    self.disconnect()
                raise
            except Exception:
                self.disconnect()
                raise
            lines = response.splitlines()
            if lines and lines[0].strip() == clean:
                lines = lines[1:]
            response = "\n".join(lines).strip()
            if CLI_ERROR.search(response):
                raise RuntimeError(response)
            return response

    def interrupt(self) -> None:
        with self._condition:
            if not self.is_connected:
                raise RuntimeError("Not connected to Flipper")
            self._serial.write(b"\x03")
            self._log("[INFO] CLI interrupt requested")

    def pop_logs(self, max_lines: int = 200) -> list[str]:
        lines: list[str] = []
        while len(lines) < max_lines:
            try:
                lines.append(self._log_queue.get_nowait())
            except queue.Empty:
                break
        return lines

    def _reader_loop(self, connection, stop: threading.Event) -> None:
        buffer = ""
        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        try:
            while not stop.is_set():
                chunk = connection.read(min(connection.in_waiting or 1, 4096))
                if not chunk:
                    continue
                buffer += decoder.decode(chunk)
                if len(buffer) > 2_000_000:
                    raise RuntimeError("CLI line exceeds 2 MB; use a smaller file")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = ANSI.sub("", line).rstrip("\r")
                    with self._condition:
                        self._response += line + "\n"
                        if len(self._response) > 2_000_000:
                            raise RuntimeError("CLI response exceeds 2 MB; use a smaller file")
                    if line:
                        self._log(line)
                if PROMPT.search(ANSI.sub("", buffer)):
                    buffer = ""
                    with self._condition:
                        self._prompt_count += 1
                        self._condition.notify_all()
        except Exception as exc:
            if not stop.is_set():
                with self._condition:
                    if self._serial is connection:
                        self._error = f"Serial read error: {exc}"
                        self._condition.notify_all()
                self._log(f"[ERROR] Serial read error: {exc}")
        finally:
            connection.close()
