# Flipper Zero Desktop Remote

Desktop-App zur Steuerung eines Flipper Zero (Momentum Firmware) auf macOS und Debian Linux.

## Aktueller Stand (V1 Full App)

- Flet-Desktop-UI mit dunklem Theme und orangefarbenem Akzent
- Bedienung ohne sichtbare CLI-Eingaben in der App (Button- und Formular-Workflows)
- Port-Scan für:
  - macOS: `/dev/cu.usbmodem*` und `/dev/tty.usbmodem*`
  - Linux: `/dev/ttyACM*`
- Connect/Disconnect, Last-Port-Merker
- Modul-Tabs: System, Remote, Storage, Infrared, NFC/RFID, Sub-GHz, BadUSB, Makros
- Remote-Tasten: Up, Down, Left, Right, OK, Back
- Long-Press mit Fallback (`long` + `press/release`)
- Quick-Actions: `device_info`, `storage list /`, Vibro, Reboot-Modi
- Log-Konsole (Statusmeldungen + kontinuierlicher Serial-Stream)
- Persistente Makros (JSON), speichern/laden/löschen/ausführen
- Expert-Mode Safety Gate für riskante Module (NFC/RFID, Sub-GHz, BadUSB)
- Modulaktionen für IR/NFC/Sub-GHz/BadUSB über direkte Buttons (z. B. Detect/Read/RX/TX/Run)

## Projektstruktur

```text
src/
  main.py
  core/
    capabilities.py
    connection_manager.py
    serial_client.py
    flipper_api.py
  persistence/
    paths.py
    config_store.py
  ui/
    app.py
packaging/
  macos/setup.py
  linux/flipper_remote.spec
  linux/flipper-remote.desktop
```

## Entwicklung (mit venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
python src/main.py
```

## Native App Build – macOS (.app)

```bash
source .venv/bin/activate
python -m pip install py2app
python packaging/macos/setup.py py2app
```

Ergebnis liegt unter `dist/Flipper Zero Desktop Remote.app`.

## Native App Build – Debian/Linux (Executable)

```bash
source .venv/bin/activate
python -m pip install pyinstaller
pyinstaller packaging/linux/flipper_remote.spec
```

Ergebnis liegt unter `dist/flipper-remote`.

Für KDE-Startmenü: `packaging/linux/flipper-remote.desktop` nach `~/.local/share/applications/` kopieren und `Exec=` auf den absoluten Pfad von `dist/flipper-remote` setzen.

## App-Daten (Persistenz)

- macOS: `~/Library/Application Support/Flipper Zero Desktop Remote`
- Linux: `$XDG_CONFIG_HOME/flipper-zero-desktop-remote` oder `~/.config/flipper-zero-desktop-remote`

Gespeichert werden:

- `settings.json` (z. B. letzter Port, Expert-Mode)
- `macros.json` (deine Makros)

## Hinweise

- Debian USB-Rechte: ggf. Nutzer zur Gruppe `dialout` hinzufügen.
- Einige Momentum-CLI-Befehle können je Firmware-Version variieren.
- Interne Modul-Aktionen senden passende Firmware-Befehle im Hintergrund; bei abweichender Momentum-Version können einzelne Aktionen andere Syntax benötigen.
- Expert-Mode nur in kontrollierten/legalen Kontexten verwenden.
