# Build-Anleitung

Diese Seite beschreibt, wie du **Flipper Zero Desktop Remote** als native, standalone Anwendung für macOS und Linux baust – ohne dass Python auf dem Zielsystem installiert sein muss.

---

## Inhaltsverzeichnis

- [Vorbereitungen](#vorbereitungen)
- [macOS – .app-Bundle (py2app)](#macos--app-bundle-py2app)
- [Linux – Executable (PyInstaller)](#linux--executable-pyinstaller)
- [Linux – Desktop-Integration](#linux--desktop-integration)

---

## Vorbereitungen

Stelle sicher, dass du eine funktionierende Entwicklungsumgebung eingerichtet hast (siehe [installation.md](installation.md)):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

---

## macOS – .app-Bundle (py2app)

`py2app` erzeugt ein vollständiges macOS-App-Bundle (`.app`), das per Doppelklick gestartet werden kann.

### 1. py2app installieren

```bash
source .venv/bin/activate
python -m pip install py2app
```

### 2. Build ausführen

```bash
python packaging/macos/setup.py py2app
```

> Der Build-Vorgang kann einige Minuten dauern.

### 3. Ergebnis

Das fertige Bundle liegt unter:

```
dist/Flipper Zero Desktop Remote.app
```

Ins `Applications`-Verzeichnis verschieben oder per Doppelklick starten:

```bash
open "dist/Flipper Zero Desktop Remote.app"
```

### Build-Konfiguration

Die Build-Konfiguration befindet sich in `packaging/macos/setup.py`. Dort können u. a. App-Name, Icon und zusätzliche Pakete angepasst werden.

### Hinweise

- Der erste Build lädt ggf. zusätzliche Abhängigkeiten herunter.
- Für eine Distribution an andere macOS-Nutzer sollte das Bundle signiert werden (erfordert Apple Developer Account).
- Gatekeeper-Warnung beim ersten Start: **Rechtsklick → Öffnen** wählen.

---

## Linux – Executable (PyInstaller)

`PyInstaller` erzeugt eine einzelne ausführbare Datei, die alle Abhängigkeiten enthält.

### 1. PyInstaller installieren

```bash
source .venv/bin/activate
python -m pip install pyinstaller
```

### 2. Build ausführen

```bash
pyinstaller packaging/linux/flipper_remote.spec
```

> Der Build-Vorgang kann einige Minuten dauern.

### 3. Ergebnis

Die fertige Executable liegt unter:

```
dist/flipper-remote
```

Direkt starten:

```bash
./dist/flipper-remote
```

Oder systemweit verfügbar machen:

```bash
sudo cp dist/flipper-remote /usr/local/bin/flipper-remote
```

### Build-Konfiguration

Die Spec-Datei `packaging/linux/flipper_remote.spec` enthält die PyInstaller-Konfiguration. Relevante Einstellungen:

| Einstellung | Bedeutung |
|---|---|
| `hiddenimports` | Pakete, die PyInstaller nicht automatisch erkennt (`flet`, `serial`, `serial.tools.list_ports`) |
| `console=False` | Kein Konsolenfenster beim Start |
| `upx=True` | UPX-Komprimierung für kleinere Dateigröße (UPX muss installiert sein) |

UPX installieren (optional, verkleinert die Executable):

```bash
sudo apt install upx
```

---

## Linux – Desktop-Integration

Für die Integration ins KDE- oder GNOME-Startmenü steht eine `.desktop`-Datei bereit.

### Desktop-Entry installieren

```bash
# Desktop-Entry kopieren
cp packaging/linux/flipper-remote.desktop ~/.local/share/applications/

# Exec-Pfad auf absolute Executable anpassen
sed -i "s|Exec=flipper-remote|Exec=$(pwd)/dist/flipper-remote|" \
    ~/.local/share/applications/flipper-remote.desktop

# Desktop-Datenbank aktualisieren
update-desktop-database ~/.local/share/applications/
```

Anschließend erscheint **Flipper Zero Desktop Remote** in der Anwendungsübersicht.

### Manuelle Anpassung

Die Datei `packaging/linux/flipper-remote.desktop` kann auch manuell bearbeitet werden:

```ini
[Desktop Entry]
Type=Application
Name=Flipper Zero Desktop Remote
Comment=Control Flipper Zero from your desktop
Exec=/absoluter/pfad/zu/dist/flipper-remote
Icon=flipper-remote
Terminal=false
Categories=Utility;Development;
```

> **Tipp:** Ein eigenes Icon kann unter `~/.local/share/icons/hicolor/256x256/apps/flipper-remote.png` abgelegt werden.
