# Flipper Zero Desktop Remote

> **Desktop-Anwendung zur komfortablen Steuerung eines Flipper Zero (Momentum Firmware) – für macOS und Debian/Ubuntu Linux.**

Mit dieser App steuerst du deinen Flipper Zero direkt vom Computer aus, ohne die winzigen Tasten am Gerät benutzen zu müssen. Alle Funktionen sind übersichtlich auf Modul-Tabs verteilt und über klare Schaltflächen erreichbar – keine manuellen CLI-Eingaben nötig.

---

## Inhaltsverzeichnis

- [Features](#features)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [Projektstruktur](#projektstruktur)
- [Dokumentation](#dokumentation)
- [Hinweise & Sicherheit](#hinweise--sicherheit)
- [Lizenz](#lizenz)

---

## Features

| Feature | Beschreibung |
|---|---|
| **Automatischer Port-Scan** | Erkennt Flipper Zero auf macOS (`/dev/cu.usbmodem*`) und Linux (`/dev/ttyACM*`) automatisch |
| **Modul-Tabs** | System · Remote · Storage · Infrared · NFC/RFID · Sub-GHz · BadUSB · Makros |
| **Remote-Steuerung** | Navigations-Buttons (Up/Down/Left/Right/OK/Back) mit Short- und Long-Press |
| **Quick-Actions** | Device-Info, Storage-Liste, Vibro, Reboot (normal / bootloader / DFU) |
| **Persistente Makros** | Befehlssequenzen per JSON speichern, laden, ausführen und löschen |
| **Log-Konsole** | Live-Anzeige aller Serial-Meldungen und Geräteantworten |
| **Expert-Mode** | Safety-Gate für riskante Module (NFC/RFID, Sub-GHz, BadUSB) |
| **Dark/Light Theme** | Wählbar; Standard: Dunkel mit orangem Akzent |
| **Persistente Einstellungen** | Letzter Port, Theme, Expert-Mode und mehr werden gespeichert |

---

## Voraussetzungen

- Python **3.10** oder neuer
- Flipper Zero mit **Momentum Firmware** (über USB verbunden)
- macOS 12+ oder Debian/Ubuntu Linux (mit `dialout`-Gruppe)

---

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote.git
cd Flipper-Zero-Desktop-Remote

# 2. Virtuelle Umgebung erstellen und aktivieren
python3 -m venv .venv
source .venv/bin/activate

# 3. Abhängigkeiten installieren
python -m pip install -U pip
python -m pip install -e .

# 4. App starten
python src/main.py
```

Flipper Zero an USB anschließen → **Scan** klicken → Port auswählen → **Connect**.

> Vollständige Installationsanleitung: [docs/installation.md](docs/installation.md)

---

## Projektstruktur

```text
Flipper-Zero-Desktop-Remote/
├── src/
│   ├── main.py                   # Einstiegspunkt
│   ├── core/
│   │   ├── capabilities.py       # Feature-Flags & Expert-Mode
│   │   ├── connection_manager.py # Port-Scan-Logik
│   │   ├── serial_client.py      # Serial-Verbindung & Reader-Thread
│   │   └── flipper_api.py        # Flipper-CLI-Befehle
│   ├── persistence/
│   │   ├── paths.py              # Plattform-Konfigurationspfade
│   │   └── config_store.py       # JSON-Einstellungen & Makros
│   └── ui/
│       └── app.py                # Flet-UI (alle Modul-Tabs)
├── packaging/
│   ├── macos/setup.py            # py2app Build-Konfiguration
│   └── linux/
│       ├── flipper_remote.spec   # PyInstaller Spec
│       └── flipper-remote.desktop # Desktop-Entry für KDE/GNOME
├── docs/                         # Ausführliche Dokumentation
├── pyproject.toml
└── README.md
```

---

## Dokumentation

Detaillierte Anleitungen und Referenzen findest du im [`docs/`](docs/)-Ordner:

| Seite | Inhalt |
|---|---|
| [Installation](docs/installation.md) | Schritt-für-Schritt-Installation auf macOS und Linux |
| [Benutzung](docs/usage.md) | UI-Übersicht, Verbindungsaufbau, Arbeiten mit Modulen |
| [Module](docs/modules.md) | Ausführliche Beschreibung aller 8 Modul-Tabs |
| [Bauen (Build)](docs/building.md) | Native App erstellen (`.app` für macOS, Executable für Linux) |
| [Konfiguration](docs/configuration.md) | Einstellungen, Makros und Datenspeicherung |
| [Mitwirken](docs/contributing.md) | Dev-Setup, Codestil und Pull-Request-Workflow |

---

## Hinweise & Sicherheit

- **Debian USB-Rechte:** Nutzer muss in der Gruppe `dialout` sein:
  ```bash
  sudo usermod -aG dialout $USER
  # Danach neu einloggen
  ```
- **Firmware-Kompatibilität:** Einige Momentum-CLI-Befehle können je Firmware-Version variieren. Bei abweichender Syntax einzelne Befehle ggf. anpassen.
- **Expert-Mode:** NFC/RFID, Sub-GHz und BadUSB sind standardmäßig durch ein Safety-Gate gesperrt. Den Expert-Mode **ausschließlich in kontrollierten und rechtlich zulässigen Umgebungen** aktivieren.
- **Keine Gewähr:** Das Projekt wird ohne jegliche Garantie bereitgestellt. Nutzung auf eigene Verantwortung.

---

## Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).
