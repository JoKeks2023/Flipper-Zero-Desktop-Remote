# Installation

Diese Seite beschreibt die vollständige Installation von **Flipper Zero Desktop Remote** auf macOS und Debian/Ubuntu Linux.

---

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Installation auf macOS](#installation-auf-macos)
- [Installation auf Debian / Ubuntu Linux](#installation-auf-debian--ubuntu-linux)
- [Flipper Zero verbinden](#flipper-zero-verbinden)
- [Bekannte Probleme](#bekannte-probleme)

---

## Voraussetzungen

| Anforderung | Version |
|---|---|
| Python | 3.10 oder neuer |
| Flipper Zero Firmware | Momentum (aktuellste empfohlen) |
| USB-Kabel | USB-A auf USB-C |

Die App benötigt folgende Python-Pakete (werden automatisch installiert):

- [`flet`](https://flet.dev/) ≥ 0.28.0 – UI-Framework
- [`flet-desktop`](https://pypi.org/project/flet-desktop/) ≥ 0.82.2 – Desktop-Backend
- [`pyserial`](https://pypi.org/project/pyserial/) ≥ 3.5 – Serial-Kommunikation

---

## Installation auf macOS

### 1. Python installieren

Falls Python noch nicht vorhanden ist, die aktuellste stabile Version von [python.org](https://www.python.org/downloads/) herunterladen und installieren, oder Homebrew nutzen:

```bash
brew install python@3.12
```

### 2. Repository klonen

```bash
git clone https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote.git
cd Flipper-Zero-Desktop-Remote
```

### 3. Virtuelle Umgebung einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Abhängigkeiten installieren

```bash
python -m pip install -U pip
python -m pip install -e .
```

### 5. App starten

```bash
python src/main.py
```

---

## Installation auf Debian / Ubuntu Linux

### 1. Python und pip sicherstellen

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

### 2. Repository klonen

```bash
git clone https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote.git
cd Flipper-Zero-Desktop-Remote
```

### 3. Virtuelle Umgebung einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Abhängigkeiten installieren

```bash
python -m pip install -U pip
python -m pip install -e .
```

### 5. USB-Rechte einrichten

Damit die App ohne Root-Rechte auf den seriellen Port zugreifen kann, muss der Benutzer der Gruppe `dialout` angehören:

```bash
sudo usermod -aG dialout $USER
```

> **Wichtig:** Nach diesem Befehl musst du dich **neu einloggen** (oder `newgrp dialout` ausführen), damit die Gruppenänderung wirksam wird.

### 6. App starten

```bash
python src/main.py
```

---

## Flipper Zero verbinden

1. Flipper Zero per USB-C-Kabel mit dem Computer verbinden.
2. App starten (`python src/main.py`).
3. Im Verbindungsbereich auf **Scan** klicken – erkannte Ports erscheinen in der Dropdown-Liste.
4. Gewünschten Port auswählen und **Connect** klicken.
5. Die Log-Konsole bestätigt die Verbindung mit `[INFO] Connected to <port> @ 115200 baud`.

> Der zuletzt verwendete Port wird in `settings.json` gespeichert und beim nächsten Start automatisch vorausgewählt.

---

## Bekannte Probleme

| Problem | Lösung |
|---|---|
| Port wird nicht erkannt (Linux) | Nutzer nicht in `dialout`-Gruppe → Schritt 5 wiederholen und neu einloggen |
| Port wird nicht erkannt (macOS) | USB-Kabel prüfen; ggf. Flipper neu starten; `ls /dev/cu.usbmodem*` im Terminal prüfen |
| `flet` startet kein Fenster | `flet-desktop` fehlt: `pip install "flet-desktop>=0.82.2"` |
| Verbindung wird sofort getrennt | Falscher Port oder Firmware-Problem; Flipper neu starten und erneut verbinden |
| Dependency-Fehler beim `pip install` | Python-Version zu alt; Python 3.10+ verwenden |
