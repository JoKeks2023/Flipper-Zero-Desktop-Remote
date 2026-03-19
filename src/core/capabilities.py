from __future__ import annotations

from dataclasses import dataclass


FEATURE_REMOTE = "remote"
FEATURE_SYSTEM = "system"
FEATURE_STORAGE = "storage"
FEATURE_INFRARED = "infrared"
FEATURE_NFC_RFID = "nfc_rfid"
FEATURE_SUBGHZ = "subghz"
FEATURE_BADUSB = "badusb"
FEATURE_MACROS = "macros"


@dataclass(frozen=True)
class FeatureCapability:
    enabled: bool
    hint: str


def build_capabilities(expert_mode: bool) -> dict[str, FeatureCapability]:
    common = {
        FEATURE_REMOTE: FeatureCapability(True, "Remote-Steuerung ist verfügbar."),
        FEATURE_SYSTEM: FeatureCapability(True, "Systemfunktionen sind verfügbar."),
        FEATURE_STORAGE: FeatureCapability(True, "Storage-Befehle sind verfügbar."),
        FEATURE_INFRARED: FeatureCapability(True, "Infrared-Befehle sind verfügbar."),
        FEATURE_MACROS: FeatureCapability(True, "Makros sind verfügbar."),
    }

    if expert_mode:
        common[FEATURE_NFC_RFID] = FeatureCapability(
            True,
            "NFC/RFID Expert-Modus aktiv. Firmware-Befehle können variieren.",
        )
        common[FEATURE_SUBGHZ] = FeatureCapability(
            True,
            "Sub-GHz Expert-Modus aktiv. Bitte regulatorische Vorgaben beachten.",
        )
        common[FEATURE_BADUSB] = FeatureCapability(
            True,
            "BadUSB Expert-Modus aktiv. Nur in kontrollierten Umgebungen verwenden.",
        )
    else:
        common[FEATURE_NFC_RFID] = FeatureCapability(
            False,
            "NFC/RFID ist in Safe-Mode deaktiviert. Aktiviere Expert-Mode in den Einstellungen.",
        )
        common[FEATURE_SUBGHZ] = FeatureCapability(
            False,
            "Sub-GHz ist in Safe-Mode deaktiviert. Aktiviere Expert-Mode in den Einstellungen.",
        )
        common[FEATURE_BADUSB] = FeatureCapability(
            False,
            "BadUSB ist in Safe-Mode deaktiviert. Aktiviere Expert-Mode in den Einstellungen.",
        )

    return common
