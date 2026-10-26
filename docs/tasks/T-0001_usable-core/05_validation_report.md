# Verifikation — 26.10.2026

## Tatsächlich ausgeführt

| Pfad | Beleg | Ergebnis |
|---|---|---|
| Native App starten | macOS `.app`-Entwicklungslauncher geöffnet; Qt-Fenster/AX-Baum sichtbar | bestanden |
| USB verbinden | UI „Verbinden“; Status „Verbunden“, Momentum mntm-012 auf Startseite | bestanden |
| Systeminformationen | vollständige CLI-Antwort, Qt-Eigenschaftsliste | bestanden |
| Live-Display | RPC-Test: 2 Frames à 1024 Bytes; anschließend echtes Menü im Qt-Fenster sichtbar | bestanden |
| Remote-Input | UI-Klick auf rechte Richtungstaste; Menübild wechselt von NFC zu Infrared, „Taste senden“ abgeschlossen | bestanden |
| CLI nach RPC | Live-Ansicht → Fernbedienungen; Geräteordner wird geladen | bestanden |
| Dateibibliothek | `/ext/infrared`: 15 gefilterte Einträge (inkl. 2 Ordner) im Qt-Browser | bestanden |
| Leerzeichen/Dateivorschau | `Canon RC-6.ir` per Tastatur gewählt; UI „Inhalt anzeigen“ zeigt 131 Bytes, Filetype/Version/name/data | bestanden |
| Qt-Seitenleiste | Accessibility-Toggle zunächst nur markiert; auf toggled umgestellt, danach Ansichtwechsel sichtbar geprüft | bestanden |
| Trennen/Neustart der Desktop-App | mehrfach geschlossen und wieder geöffnet, Port jeweils erneut verfügbar | bestanden |
| Installation | `pip install -e .`, Flet aus Projektumgebung entfernt, `pip check` | bestanden |

## Automatisierte Regression

`QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v`

Abdeckung: CLI-Antwortgrenzen, fragmentiertes UTF-8/Prompt, Firmwarefehler,
Timeout/Interrupt/Folgekommando, Geräteverlust, konkurrierende Aufrufer,
Dateinamen/Größen/Pfade, RPC-Framing/Input/Bitmap, native Qt-Verbindung,
Browser/Vorschau/Disconnect, Hauptthread-Callbacks, Easy Mode, Makros, JSON.
Zusätzlich Syntaxprüfung und `git diff --check`.
Finaler Lauf: **23 Tests bestanden**. Syntaxprüfung und Diff-Prüfung ebenfalls grün.

## Nicht vollständig verifiziert

- Linux: CI-Konfiguration angelegt; kein Linux-Lauf oder USB-Test in dieser Sitzung.
- Standalone-PyInstaller-Bundles: Specs angepasst, kein Build/Signierung/Notarisierung.
- Geräte-App-Start aus IR/NFC/Sub-GHz/BadUSB-Bibliotheken: anhand Firmwarequelle
  implementiert, nicht Teil der Geräteabnahme. Kein Senden, Emulieren, Schreiben
  von Tags oder Ausführen von BadUSB im Test.
- Hardware-Abziehen wurde durch einen Transportfehler simuliert, nicht physisch
  während der Abnahme ausgeführt. Andere Momentum-Versionen nicht geprüft.
- Vollständige Funktionsparität für jede Geräte-App ist nicht nachgewiesen.
