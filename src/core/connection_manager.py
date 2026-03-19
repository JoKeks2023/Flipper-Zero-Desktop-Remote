from __future__ import annotations

import platform
from typing import List

from serial.tools import list_ports


def _preferred_prefixes() -> tuple[str, ...]:
    system = platform.system().lower()
    if system == "darwin":
        return ("/dev/cu.usbmodem", "/dev/tty.usbmodem")
    if system == "linux":
        return ("/dev/ttyACM",)
    return ()


def scan_flipper_ports() -> List[str]:
    prefixes = _preferred_prefixes()
    found: list[str] = []
    fallback: list[str] = []

    for port in list_ports.comports():
        device = port.device or ""
        description = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()

        if prefixes and device.startswith(prefixes):
            found.append(device)
            continue

        if "flipper" in description or "flipper" in manufacturer:
            fallback.append(device)

    unique = []
    for value in [*found, *fallback]:
        if value and value not in unique:
            unique.append(value)
    return unique
