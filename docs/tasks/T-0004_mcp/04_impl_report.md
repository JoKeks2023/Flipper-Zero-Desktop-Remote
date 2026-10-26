# Umsetzung — 26.10.2026

## MCP

- Optionales offizielles SDK 2.3.0, stdio-Starter `flipper-remote-mcp` und sechs Tools.
- `flipper_mcp/ipc.py`: private lokale Verbindung, begrenzte Nachrichten/Clients,
  20 Sekunden Verbindungsfrist, 0700-Verzeichnis und Besitzersperre.
- Stabiler Socketpfad ohne Abhängigkeit von TMPDIR, das MCP-Hosts herausfiltern können.
- `ui/mcp_controller.py`: gemeinsame Qt-Warteschlange und bestehende USB-Verbindung.
  Keine zweite Serial-Verbindung durch den MCP-Prozess. Frische Statusabfragen
  aktualisieren dasselbe Dashboard; Speicherabfragen unterbrechen keine Live-Ansicht.
- Lesen und Bedienung getrennt. Rechte bei der Ausführung geprüft, Widerruf schließt
  Client-Verbindungen. Begrenzte Textvorschau entfernt die echte CLI-`Size:`-Kopfzeile.
- PNG-Bildinhalt mit Zeitangabe. Fehler als MCP-Fehlerresultat; kein Auto-Retry.
- Globale KI-Client-Konfigurationen wurden nicht verändert. App liefert TOML/JSON zum Kopieren.

## Einstellungen und Veröffentlichungsvorbereitung

- Vier native Tabs: Allgemein, Gerät, KI-Anbindung, Über.
- Theme/Bedienmodus, Startseite, 5/10/30 Sekunden oder manueller Gerätestatus,
  optionale Verbindung zum exakt zuletzt verwendeten Port.
- Easy Mode zeigt Übersicht als Startseite; die separate Startseitenwahl für
  Alle Werkzeuge wird durch Änderungen im Easy Mode nicht überschrieben.
- USB-Auswahl und Verbinden/Trennen in den Geräteeinstellungen; Expert-Mode getrennt.
- Datenordner öffnen und bewusst begrenzte Diagnose zum Kopieren.
- Tab-Navigation erreicht auch Auswahlfelder innerhalb der App.
- Über-Seite mit Version, Projekt-/Fehler-/Release-Links, Datenhinweisen und Credits.
- Vom Nutzer gewählte MIT-Lizenz, SPDX-Paketmetadaten, Ressourcen im Lizenzdialog und
  Paketkonfigurationen. Abhängigkeiten behalten ihre eigenen Lizenzen.
- Keine automatische Veröffentlichung, Signierung oder neue Update-Infrastruktur.

Tracking: GitHub #4. Linux-/Standalone-Abnahme aus T-0001 bleibt separat offen.
