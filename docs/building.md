# App-Pakete

## macOS: Entwicklungslauncher

```bash
python packaging/macos/create_launcher.py
open "build/Flipper Zero Desktop Remote.app"
```

Kleiner `.app`-Launcher ohne Kompilierung. Benötigt dieses Checkout und dessen
`.venv`. Nach Verschieben des Checkout den Launcher neu erstellen. Dieser Weg
wurde lokal mit der echten App geprüft.

Der optionale MCP-Server wird separat mit `python -m pip install -e '.[mcp]'`
installiert (Python 3.11+). Ein späteres eingefrorenes Desktop-Paket nutzt den
separat installierten `flipper-remote-mcp`-Starter; ein MCP-Standalone-Binary ist
noch nicht Teil der Paketierung.

## Eigenständige Pakete (Build-Konfiguration, noch nicht abgenommen)

```bash
python -m pip install -e '.[dev]'
# Auf macOS:
pyinstaller --noconfirm packaging/macos/flipper_remote.spec
# Auf Linux:
pyinstaller --noconfirm packaging/linux/flipper_remote.spec
```

Build jeweils auf dem Zielbetriebssystem. Qt-Widgets-Plugins werden durch die
PyInstaller-Hooks eingesammelt; WebEngine wird ausgeschlossen. Die alte py2app-
Konfiguration ist ersetzt. Keine lokalen Standalone-Builds in dieser Sitzung:
Signierung, Notarisierung, Linux-Distribution und Installation auf einem sauberen
Zielgerät sind vor einer Veröffentlichung noch zu prüfen.

Qt/PySide6-Lizenz- und Weitergabebedingungen sind bei Release-Paketen zu berücksichtigen:
[Qt for Python Licensing](https://doc.qt.io/qtforpython-6/licenses.html).
Die Projektquellen sind MIT-lizenziert. `LICENSE`, `THIRD_PARTY_NOTICES.md` und die
UI-Lizenztexte werden im Python-Wheel mitgeliefert; die PyInstaller-Konfigurationen
nehmen die UI-Texte ebenfalls auf. Für echte Binärpakete sind zusätzlich die
Lizenzdateien aller tatsächlich gebündelten Komponenten mitzuliefern.
