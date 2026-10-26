# Installation

Python 3.10–3.15 und Qt/PySide6-Essentials 6.12.0. Empfohlen: Python 3.12.
Python 3.12 muss vor dem folgenden Schritt installiert sein; `python3.12` kann
durch einen vorhandenen unterstützten Python-Interpreter ersetzt werden.
macOS 14+; für Linux ein aktuelles Debian/Ubuntu mit grafischer Sitzung.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
flipper-remote
```

Die Qt-Wheels enthalten die Widget-Laufzeit. Qt WebEngine wird nicht benötigt.
Die App benötigt keine Netzwerkverbindung zum Betrieb, nur das USB-Gerät.

Linux: Der Benutzer benötigt Zugriff auf `/dev/ttyACM*`, üblicherweise über `dialout`:

```bash
sudo usermod -aG dialout "$USER"
```

Danach neu anmelden. Falls Qt über fehlende Systembibliotheken klagt (Ubuntu):

```bash
sudo apt install libegl1 libopengl0 libxkbcommon-x11-0 libxcb-cursor0
```

Bei **Resource busy** qFlipper, Firmware-Updater oder andere Serial-Programme schließen.
Bei leerer Portliste Kabel, Firmwarezustand und USB-Rechte prüfen. Auf Linux ist
`QT_QPA_PLATFORM=offscreen` nur für Tests gedacht, nicht für die interaktive App.

macOS-Doppelklick-Launcher: siehe [Build](building.md).
