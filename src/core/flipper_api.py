from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class KeyAction:
    key: str
    action_type: str = "short"


class FlipperAPI:
    def __init__(self, send_command):
        self._send_command = send_command

    def raw(self, command: str) -> None:
        self._send_command(command)

    def vibro(self, enabled: bool) -> None:
        self._send_command(f"vibro {1 if enabled else 0}")

    def set_led(self, red: int, green: int, blue: int) -> None:
        self._send_command(f"led set {red} {green} {blue}")

    def device_info(self) -> None:
        self._send_command("device_info")

    def storage_list(self, path: str = "/") -> None:
        self._send_command(f"storage list {path}")

    def reboot_normal(self) -> None:
        self._send_command("power reboot")

    def reboot_bootloader(self) -> None:
        self._send_command("power reboot2bootloader")

    def reboot_firmware_update(self) -> None:
        self._send_command("power reboot2dfu")

    def input_send(self, key: str, action_type: str = "short") -> None:
        self._send_command(f"input send {key} {action_type}")

    def input_long_with_fallback(self, key: str, hold_seconds: float = 0.4) -> None:
        self._send_command(f"input send {key} long")
        time.sleep(0.03)
        self._send_command(f"input send {key} press")
        time.sleep(max(0.1, hold_seconds))
        self._send_command(f"input send {key} release")
