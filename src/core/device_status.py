"""Read-only device telemetry, with units from Flipper's Power HAL v2 / debug v1.

See targets/f7/furi_hal/furi_hal_power.c and furi_hal_power.h in the firmware.
Keep each source separate: a USB connection does not imply that the battery charges.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import math


def parse_properties(response: str) -> dict[str, str]:
    result = {}
    for line in response.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip():
                result[key.strip()] = value.strip()
    return result


@dataclass(frozen=True)
class DeviceStatus:
    device: dict[str, str] = field(default_factory=dict)
    power: dict[str, str] = field(default_factory=dict)
    debug: dict[str, str] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    received_at: datetime | None = None

    def number(self, key: str, *, debug=False, minimum=None, maximum=None):
        values = self.debug if debug else self.power
        # A future incompatible format must not silently acquire today's units.
        if values.get("format.major") != ("1" if debug else "2"):
            return None
        try:
            value = float(values[key])
        except (KeyError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        if minimum is not None and value < minimum:
            return None
        if maximum is not None and value > maximum:
            return None
        return value

    @property
    def charge_level(self):
        return self.number("charge.level", minimum=0, maximum=100)

    @property
    def charge_state(self):
        if self.power.get("format.major") != "2":
            return "Nicht verfügbar"
        return {"charging": "Wird geladen", "charged": "Voll geladen",
                "discharging": "Lädt nicht"}.get(self.power.get("charge.state"), "Nicht verfügbar")


def read_device_status(send_command, cancelled=lambda: False) -> DeviceStatus:
    values, errors = {}, {}
    for source, command in (("device", "device_info"), ("power", "info power"),
                            ("debug", "info power_debug")):
        if cancelled():
            raise InterruptedError("Aktualisierung abgebrochen")
        try:
            values[source] = parse_properties(send_command(command, timeout=4))
            if not values[source]:
                errors[source] = "Keine Daten erhalten"
        except InterruptedError:
            raise
        except Exception as exc:
            # Unsupported power commands must not prevent using the connected device.
            values[source] = {}
            errors[source] = str(exc)
    for source, major in (("power", "2"), ("debug", "1")):
        if values[source] and values[source].get("format.major") != major:
            errors[source] = "Unbekanntes Datenformat"
    return DeviceStatus(**values, errors=errors, received_at=datetime.now().astimezone())


def measurement(value, unit, decimals=0):
    if value is None:
        return "—"
    return f"{value:.{decimals}f}".replace(".", ",") + " " + unit
