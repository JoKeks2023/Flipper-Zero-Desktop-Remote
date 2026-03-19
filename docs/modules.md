# Module

Detaillierte Beschreibung aller acht Modul-Tabs in **Flipper Zero Desktop Remote**.

---

## Inhaltsverzeichnis

- [System](#system)
- [Remote](#remote)
- [Storage](#storage)
- [Infrared](#infrared)
- [NFC / RFID](#nfc--rfid)
- [Sub-GHz](#sub-ghz)
- [BadUSB](#badusb)
- [Makros](#makros)

---

## System

**Zugang:** Immer verfügbar

Das System-Modul bietet grundlegende Gerätefunktionen und Statusinformationen.

### Verfügbare Aktionen

| Aktion | Flipper-Befehl | Beschreibung |
|---|---|---|
| **Device Info** | `device_info` | Zeigt Hardware-Version, Firmware, Serial-Nummer u. a. |
| **Storage List** | `storage list /` | Listet den Inhalt des Root-Verzeichnisses |
| **Vibro an** | `vibro 1` | Vibration einschalten |
| **Vibro aus** | `vibro 0` | Vibration ausschalten |
| **Reboot** | `power reboot` | Normaler Neustart |
| **Reboot → Bootloader** | `power reboot2bootloader` | Neustart in den Bootloader-Modus |
| **Reboot → DFU** | `power reboot2dfu` | Neustart in den Firmware-Update-Modus (DFU) |

> **Hinweis:** Reboot-Befehle trennen die Serial-Verbindung. Nach dem Neustart muss die Verbindung erneut aufgebaut werden.

---

## Remote

**Zugang:** Immer verfügbar

Das Remote-Modul ermöglicht die vollständige Navigation des Flipper Zero vom Desktop aus – als wärst du direkt am Gerät.

### Navigationstasten

| Taste | Befehl (Short) | Befehl (Long) |
|---|---|---|
| ↑ Up | `input send up short` | `input send up long` |
| ↓ Down | `input send down short` | `input send down long` |
| ← Left | `input send left short` | `input send left long` |
| → Right | `input send right short` | `input send right long` |
| OK | `input send ok short` | `input send ok long` |
| Back | `input send back short` | `input send back long` |

### Long-Press-Verhalten

Long-Press nutzt einen Fallback-Mechanismus für maximale Kompatibilität:

1. `input send <key> long` wird gesendet
2. Kurze Pause (30 ms)
3. `input send <key> press` wird gesendet
4. Wartezeit (≥ 100 ms, konfigurierbar)
5. `input send <key> release` wird gesendet

---

## Storage

**Zugang:** Immer verfügbar

Das Storage-Modul ermöglicht das Browsen des internen Dateisystems des Flipper Zero.

### Verfügbare Aktionen

| Aktion | Beschreibung |
|---|---|
| **List** | Verzeichnisinhalt für den eingegebenen Pfad auflisten |
| **Read** | Datei lesen und Inhalt in der Log-Konsole anzeigen |
| **Stat** | Metadaten einer Datei oder eines Verzeichnisses anzeigen |

### Wichtige Pfade

| Pfad | Inhalt |
|---|---|
| `/` | Root-Verzeichnis |
| `/ext/` | SD-Karte |
| `/int/` | Interner Flash-Speicher |
| `/ext/infrared/` | Gespeicherte IR-Dateien |
| `/ext/nfc/` | NFC-Daten |
| `/ext/subghz/` | Sub-GHz-Dateien |
| `/ext/badusb/` | BadUSB-Skripte |

---

## Infrared

**Zugang:** Immer verfügbar

Das Infrared-Modul steuert den IR-Transceiver des Flipper Zero.

### Verfügbare Aktionen

| Aktion | Beschreibung |
|---|---|
| **Detect** | IR-Signalempfang starten (Signale aufzeichnen) |
| **RX** | Empfangsmodus aktivieren |
| **TX** | Gespeichertes IR-Signal senden |
| **Stop** | Laufende IR-Aktion beenden |

> IR-Dateien (`.ir`) liegen auf der SD-Karte unter `/ext/infrared/`. Für das Senden muss ein Dateiname oder Signalname angegeben werden.

---

## NFC / RFID

**Zugang:** Nur im Expert-Mode  
**Safety-Gate:** Muss explizit in den Einstellungen freigeschaltet werden

Das NFC/RFID-Modul bietet Zugriff auf den NFC-Chip und RFID-Leser des Flipper Zero.

### Verfügbare Aktionen

| Aktion | Beschreibung |
|---|---|
| **Detect** | Karte/Tag in der Nähe erkennen |
| **Read** | NFC-Karte oder RFID-Tag lesen |
| **Write** | Daten auf eine Karte schreiben |
| **Emulate** | Gespeicherte Karte emulieren |
| **Stop** | Laufende Aktion beenden |

> ⚠️ Das Lesen, Schreiben und Emulieren von NFC/RFID-Tags kann rechtlich eingeschränkt sein. Nur auf eigenen Karten und in zulässigen Umgebungen verwenden.

---

## Sub-GHz

**Zugang:** Nur im Expert-Mode  
**Safety-Gate:** Muss explizit in den Einstellungen freigeschaltet werden

Das Sub-GHz-Modul steuert den CC1101-Transceiver für Frequenzen im Sub-GHz-Bereich (315 / 433 / 868 MHz).

### Verfügbare Aktionen

| Aktion | Beschreibung |
|---|---|
| **RX** | Empfangsmodus aktivieren (Signale aufzeichnen) |
| **TX** | Gespeichertes Sub-GHz-Signal senden |
| **Analyze** | Empfangenes Signal analysieren |
| **Stop** | Laufende Aktion beenden |

> ⚠️ Das Senden auf Sub-GHz-Frequenzen ist in vielen Ländern reguliert. Der Betrieb auf lizenzierten Frequenzen ohne entsprechende Genehmigung ist illegal. Bitte die geltenden Funkregelungen einhalten.

---

## BadUSB

**Zugang:** Nur im Expert-Mode  
**Safety-Gate:** Muss explizit in den Einstellungen freigeschaltet werden

Das BadUSB-Modul startet Ducky-Script-Payloads, die der Flipper Zero als USB-HID-Gerät ausführt.

### Verfügbare Aktionen

| Aktion | Beschreibung |
|---|---|
| **Run** | BadUSB-Skript aus `/ext/badusb/` ausführen |
| **List** | Verfügbare Skripte auflisten |
| **Stop** | Laufendes Skript abbrechen |

> ⚠️ BadUSB-Skripte führen Tastatureingaben auf dem angeschlossenen Computer aus. Nur auf eigenen Geräten und in vollständig kontrollierten Umgebungen verwenden. Das Ausführen von BadUSB-Skripten auf fremden Systemen ist illegal.

---

## Makros

**Zugang:** Immer verfügbar

Das Makros-Modul ermöglicht das Erstellen, Speichern und Ausführen von Befehlssequenzen.

### Funktionen

| Funktion | Beschreibung |
|---|---|
| **Neu** | Makro-Namen und Befehlsliste eingeben und speichern |
| **Ausführen** | Ausgewähltes Makro als Befehlssequenz an den Flipper senden |
| **Löschen** | Ausgewähltes Makro permanent entfernen |
| **Laden** | Makros aus `macros.json` neu laden |

### Makro-Format

Makros werden als JSON-Objekt gespeichert. Jeder Eintrag besteht aus einem Namen und einer Liste von Befehlen:

```json
{
  "Status": [
    "device_info",
    "storage list /"
  ],
  "Quick Reboot": [
    "power reboot"
  ],
  "Mein Makro": [
    "vibro 1",
    "input send ok short",
    "vibro 0"
  ]
}
```

> Speicherort der Makro-Datei: siehe [configuration.md](configuration.md)
