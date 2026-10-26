# App-Pakete bauen und prüfen

Die Release-Pakete werden mit Python 3.12 auf GitHub Actions gebaut:
[Desktop packages](https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/actions/workflows/packages.yml).
Matrix: macOS 15 arm64, macOS 15 Intel und Ubuntu 24.04 x86_64.

## Eigenständige Pakete

Im Checkout auf dem jeweiligen Zielsystem:

```bash
python -m pip install -e '.[dev,mcp]'
python packaging/collect_licenses.py
QT_QPA_PLATFORM=offscreen python packaging/create_icons.py
# macOS:
pyinstaller --noconfirm packaging/macos/flipper_remote.spec
# Linux:
pyinstaller --noconfirm packaging/linux/flipper_remote.spec
```

Die Lizenzsammlung lädt Notices aus den installierten Distributionen und den passenden offiziellen Qt-Quellen. Fehlen sie im Wheel, wird das zugehörige Source-Archiv geladen. URLs, Prüfsummen und Versionen stehen in `build/release-licenses/BUILD-ENVIRONMENT.json`. Dieses Inventar umfasst auch Build-Werkzeuge; es ist eine Obermenge der tatsächlich gebündelten Komponenten. [Komponenten und Austausch](binary-components.md).

Qt WebEngine und Tk werden ausgeschlossen. Die Qt-Widgets-Laufzeit bleibt dynamisch geladen. Der eingebettete MCP wird über dasselbe Programm mit `--mcp` gestartet; die App erzeugt dafür eine absolute Client-Konfiguration.

## Verifikation

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
# macOS:
python packaging/smoke_bundle.py 'dist/Flipper Zero Desktop Remote.app/Contents/MacOS/flipper-remote'
# Linux:
python packaging/smoke_bundle.py dist/flipper-remote/flipper-remote
```

Der Pakettest startet den **erzeugten** MCP-Prozess: Handshake, sechs Tools, verständlicher Fehler ohne Desktop-Verbindung. Anschließend erzeugt er alle echten Qt-Seiten, wechselt beide Themes, prüft die Mindestbreite und lädt die Lizenztexte und das App-Symbol. Dabei verwendet er temporäre Einstellungen und keine USB-Verbindung. `--smoke-test` ist ausschließlich dieser Entwicklercheck.

Für die Geräteabnahme das entpackte Paket regulär starten, verbinden und die betroffenen Wege sichtbar prüfen. CI ersetzt keine Hardware-Abnahme.

## Archivieren und Signieren

macOS: `ditto -c -k --sequesterRsrc --keepParent` erhält die Bundle-Links. Linux: den kompletten Ordner mit `tar -czf` packen. Einzelne Programmdateien reichen nicht aus. Siehe [PyInstaller zu symbolischen Links](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#requirements-imposed-by-symbolic-links-in-frozen-application).

Die erste Vorschau verwendet PyInstallers Ad-hoc-Signatur auf macOS. Eine Developer-ID-Signatur und Notarisierung sind noch nicht eingerichtet. Keine App-Store-Veröffentlichung.

## Leichter macOS-Entwicklungslauncher

```bash
python packaging/macos/create_launcher.py
open "build/Flipper Zero Desktop Remote.app"
```

Dieser Launcher benötigt das Checkout und dessen `.venv`; er ist kein Release-Paket. Nach Verschieben des Checkout neu erstellen.
