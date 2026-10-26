# Installation

[Downloads für v0.2.0](https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/releases/tag/v0.2.0).
Die Desktop-Pakete enthalten Python, Qt und den MCP-Server. Eine Python-Installation ist dafür nicht nötig.

## macOS

1. Passendes ZIP laden: **arm64** für Apple Silicon, **x86_64** für Intel. macOS 14 oder neuer.
2. ZIP im Finder entpacken; **Flipper Zero Desktop Remote.app** nach **Programme** ziehen.
3. App öffnen. Flipper per USB verbinden; qFlipper und Firmware-Updater vorher schließen.
4. In der App **Verbinden** wählen.

Die Vorschau ist ad hoc signiert, aber nicht mit einer Apple-Entwickleridentität signiert und nicht notarisiert. Gatekeeper kann den Start daher blockieren. Wer der heruntergeladenen Datei vertraut und die Prüfsumme kontrolliert hat, kann nach dem ersten Startversuch unter **Systemeinstellungen → Datenschutz & Sicherheit → Dennoch öffnen** eine Ausnahme für diese App erlauben. [Apples Anleitung](https://support.apple.com/de-at/102445).

Die Systemeinstellungen nicht global abschalten. Eine Warnung über erkannte Schadsoftware nicht übergehen; stattdessen Datei und Downloadquelle prüfen.

## Linux

Das x86_64-Paket wird auf **Ubuntu 24.04** gebaut und dort ohne Hardware gestartet. Ältere Distributionen und Linux arm64 sind in dieser Vorschau nicht abgenommen.

```bash
tar -xzf Flipper-Remote-0.2.0-linux-x86_64.tar.gz
./flipper-remote/flipper-remote
```

Den gesamten Ordner zusammenlassen. Die enthaltenen Qt-Bibliotheken und symbolischen Links sind Teil des Pakets.

Ubuntu benötigt gegebenenfalls diese Bibliotheken:

```bash
sudo apt install libegl1 libopengl0 libxkbcommon-x11-0 libxcb-cursor0
```

Der Benutzer benötigt Zugriff auf `/dev/ttyACM*`, unter Ubuntu üblicherweise über die Gruppe `dialout`:

```bash
sudo usermod -aG dialout "$USER"
```

Danach ab- und wieder anmelden. Die App als normaler Benutzer starten.
Die mitgelieferte `.desktop`-Datei ist eine Vorlage: `Exec` und `Icon` auf die absoluten Pfade des entpackten Pakets setzen und die Datei bei Bedarf unter `~/.local/share/applications/` ablegen.

## Download prüfen

Neben den Paketen liegt `SHA256SUMS.txt` im Release. Im Downloadordner:

```bash
# macOS:
shasum -a 256 Flipper-Remote-0.2.0-macos-arm64.zip
# Linux:
sha256sum Flipper-Remote-0.2.0-linux-x86_64.tar.gz
```

Ergebnis mit dem passenden Eintrag in `SHA256SUMS.txt` vergleichen. Die Prüfsumme erkennt beschädigte oder abweichende Dateien; sie ersetzt keine Herausgebersignatur.

## Aus dem Quellcode

Python **3.10–3.15**; MCP benötigt **3.11+**. Empfohlen: Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mcp]'
flipper-remote
```

Ohne MCP genügt `python -m pip install -e .`. Die Qt-Wheels enthalten die Widget-Laufzeit.

## Verbindung und Updates

Bei **Resource busy** qFlipper, Firmware-Updater oder andere Serial-Programme schließen. Bei leerer Portliste Kabel, Firmwarezustand und USB-Rechte prüfen. `QT_QPA_PLATFORM=offscreen` ist nur für Tests gedacht.

Für ein Update die App beenden und das Paket ersetzen. Einstellungen und Makros liegen außerhalb des App-Pakets und bleiben erhalten; den Ordner findest du unter **Einstellungen → Allgemein → Datenordner öffnen**. Die Vorschau enthält keinen automatischen Updater.
