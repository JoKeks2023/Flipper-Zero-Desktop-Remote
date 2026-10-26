# Flipper Zero Desktop Remote

Natives Control Center für Flipper Zero mit Momentum: **Qt Widgets / PySide6**, für
macOS und Linux. Keine WebView, kein Flet, kein lokaler Webserver.

## Was die App kann

- **Easy Mode:** Aufgaben statt CLI, vereinfachte Navigation, technische Details ausgeblendet.
- **Geräte-Dashboard:** Akkustand, Ladezustand, USB-/Akku-/Systemspannung, Strom,
  Temperatur, Akkugesundheit, Kapazitäten und Geräte-/Firmwaredaten. Echte Messwerte,
  manuelle und automatische Aktualisierung, vollständige Rohdaten auf Wunsch.
- **Live-Fernbedienung:** echtes 128 × 64 Display über USB, kurze/lange Tastendrücke.
  Damit lassen sich die Geräte-Menüs und dort verfügbare Funktionen am Desktop bedienen.
- **Dateibrowser:** echte Ordner/Dateien, Unterordner, Textvorschau, Ordner erstellen,
  Löschen nach Bestätigung. Keine erfundenen Beispieldateien.
- **Modulbibliotheken:** IR, NFC, Sub-GHz und BadUSB-Dateien filtern und ansehen;
  Start in der passenden Geräte-App mit anschließender Live-Bedienung.
- **System:** Geräte- und Firmwareinformationen, laufende App abfragen, Neustart.
- **Makros:** lokale Befehlsfolgen, Antworten abwarten, abbrechen, speichern/löschen.
- **Einstellungen:** System/Hell/Dunkel, Startmodul, Easy Mode und Expert-Mode getrennt.

Der Desktop ersetzt nicht die Flipper-Hardware: USB-Kabel, Empfangsreichweite,
Antenne, IR-Ausrichtung und gerätespezifische Grenzen bleiben bestehen. Nicht jede
Gerätefunktion besitzt schon einen eigenen Desktop-Dialog; dafür gibt es das
Live-Display. Expert-Mode ist eine Bedienhilfe, keine Sicherheitsgrenze.

## Starten

Python **3.10–3.15**, macOS **14+** oder aktuelles Debian/Ubuntu Linux.
Für die Entwicklung ist Python 3.12 empfohlen.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
flipper-remote
```

Alternativ: `python src/main.py`. qFlipper vor dem Verbinden schließen.
Easy Mode startet mit **Verbinden**; bei mehreren Ports erscheint eine Auswahl.

macOS-Entwicklungslauncher als doppelklickbare App:

```bash
python packaging/macos/create_launcher.py
open "build/Flipper Zero Desktop Remote.app"
```

Dieser Launcher benötigt das Checkout und dessen `.venv`; er ist kein eigenständig
verteilbares Release. Standalone-Builds: [Build-Anleitung](docs/building.md).

## Verifikation und Grenzen

Am 26.10.2026 mit angeschlossenem Momentum **mntm-012** auf macOS geprüft:
USB-Geräteinformationen, echte Dateilisten, Display-Streaming und Remote-Eingabe.
Das Dashboard wurde ebenfalls mit realen Akku- und Power-Messwerten geprüft.
Tests ohne Hardware prüfen unter anderem Antwortgrenzen, Timeout/Abbruch,
Dateinamen mit Leerzeichen, Qt-Worker und lokale Speicherung.

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Linux ist Zielplattform; eine lokale Linux-Geräteprüfung und die Standalone-
Pakete wurden in dieser Sitzung nicht ausgeführt. CI ist für macOS/Linux angelegt.
Kein Nachweis für Senden, Emulieren oder BadUSB-Ausführung durch diese Abnahme.

## Dokumentation

[Installation](docs/installation.md) · [Benutzung](docs/usage.md) ·
[Module](docs/modules.md) · [Konfiguration](docs/configuration.md) ·
[Build](docs/building.md) · [Mitwirken](docs/contributing.md) ·
[Umsetzung und Abnahme](docs/tasks/T-0001_usable-core/00_brief.md)
