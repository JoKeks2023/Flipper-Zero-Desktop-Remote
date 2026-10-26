# Entwicklung

Python 3.12 empfohlen. Installation: `python -m pip install -e .`.
Start: `flipper-remote` oder `python src/main.py`.

- `src/core/serial_client.py`: ein Reader, CLI-Transaktionen bis zum Geräte-Prompt,
  Timeout mit Interrupt, Verbindungsfehler und begrenztes Protokoll.
- `src/core/rpc_display.py`: begrenzter Protobuf-Subset für Live-Display und Input.
- `src/core/storage.py`: typisierte Dateieinträge; Pfade mit Leerzeichen.
- `src/ui/app.py`: Qt-Hauptfenster, Easy Mode und Ablaufsteuerung.
- `src/ui/browser.py`, `screen.py`, `sidebar.py`: wiederverwendbare native Widgets.
- `src/ui/jobs.py`: Qt-Worker; UI-Updates ausschließlich im Hauptthread.
- `src/persistence/`: bestehende lokale JSON-Dateien, atomare Speicherung.

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Tests verwenden simulierte Transportantworten und echte Qt-Widgets; kein Gerät
und kein Simulator nötig. CI deckt macOS und Linux ab. Grünes CI ersetzt keine
USB- und sichtbare UI-Abnahme. Bei Protokolländerungen Firmwarequelle und
angeschlossenes Gerät prüfen. Keine Squash-Merges.

Operative Übergabe: `docs/tasks/T-0001_usable-core/`.
