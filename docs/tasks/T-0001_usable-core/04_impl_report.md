# Umsetzung — 26.10.2026

## Änderungen

- Flet ersetzt durch Qt Widgets / PySide6-Essentials 6.12.0. Kein WebEngine.
- Neue Aufgaben-Startseite, Seitenleiste, klare Titel/Abstände, System/Hell/Dunkel.
- Easy Mode (Default): vereinfachte Namen, keine CLI/Systemdetails/freien Makros;
  Expert-Mode bleibt ein unabhängiger Schalter. Portauswahl nur bei mehreren Geräten.
- Echte Live-Fernbedienung: RPC-Screenstream, 128×64-Bitmap, Orientierung,
  Input-Sequenz press/short oder long/release. Native Anzeige, Remote-Tastaturbedienung.
- Dateibrowser je Modul mit Unterordnern, Pfad-Select, Textvorschau, Bestätigung vor
  Löschaktionen. Verbindungswechsel RPC → CLI automatisch vor Dateiaktionen.
- Transaktionen warten auf CLI-Prompt statt feste Pausen; Fehler/Timeout/Interrupt,
  UTF-8-Fragmente, Antwort-/Loggrößen begrenzt, Reader räumt Verbindung auf.
- Qt-Worker halten Geräteabfragen vom UI-Thread fern; Signale zurück in Hauptthread.
- Makros seriell, Abbruch stoppt Folgeschritte; lesende/navigation Befehle ohne Expert,
  freie Makros nur mit Expert-Mode und Bestätigung.
- JSON atomar; partielle Settings ergänzen; letztes gelöschtes Makro bleibt gelöscht.
- Startkommando `flipper-remote`, macOS-Entwicklungslauncher, neue PyInstaller-Specs,
  CI für macOS/Linux und Dokumentation angepasst.

## Explizite Verhaltensänderungen

- Ungültige direkte IR-/NFC-/BadUSB-CLI-Aktionen durch Geräte-App-Start plus Live-
  Bedienung ersetzt. Vollständige eigene Desktop-Dialoge dafür noch nicht implementiert.
- Legacy `accent`/`density` bleiben gespeichert, werden in Qt nicht mehr ausgewertet.
- Expert-Mode ist keine Zugriffskontrolle: Live-Remote bedient die Geräte-Menüs.
- Voraussetzungen jetzt gemäß Qt-Wheels: macOS 14+, Python 3.10–3.15.

## Nachverfolgung

GitHub #2: native nutzbare Basis; GitHub #3: Makro-/Settings-Speicherfehler.
Huly ist in dieser Sitzung nicht verfügbar. Keine Statusänderung dort behauptet.
Kein Merge, kein Push im Rahmen dieser lokalen Übergabe. Commit siehe Git-Historie.
