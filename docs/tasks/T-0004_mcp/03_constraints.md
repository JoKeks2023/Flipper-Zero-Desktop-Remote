# Grenzen und Quellen

- macOS/Linux, native Qt-Widgets; keine Simulatoren oder schweren Builds.
- Standardinstallation der UI behält Python 3.10; optionaler MCP benötigt Python 3.11+.
- Offizielles SDK 2.3.0 als optionales Extra, am 26.10.2026 gegen PyPI geprüft.
- Nur lokale stdio-Verbindung über benutzereigenen privaten Unix-Socket (0700-Ordner).
  Kein HTTP-Listener, keine Cloud-Veröffentlichung, kein eigenmächtiger Client-Config-Write.
- Gerätedaten und Dateiinhalte sind untrusted content; keine daraus abgeleitete Ausführung.
- Tasten können Geräteaktionen auslösen und brauchen die separate Freigabe in der App.
- Keine automatische Wiederholung bei Zeitüberschreitung oder Verbindungsverlust.
- Quellen: [SDK](https://py.sdk.modelcontextprotocol.io/),
  [Transporte](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports),
  [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools).
- Codex-stdio-Einrichtung lokal gegen `codex mcp add --help` geprüft.
