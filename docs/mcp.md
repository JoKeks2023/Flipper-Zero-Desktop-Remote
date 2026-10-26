# MCP: Flipper über die Desktop-App verwenden

Die Desktop-App hält die USB-Verbindung. Ein MCP-Client startet den separaten
stdio-Server `flipper-remote-mcp`, der ausschließlich mit dieser App kommuniziert.
Dadurch bleiben Oberfläche und KI-Zugriff synchron; kein zweiter Prozess öffnet USB.

## Einrichtung

In den Desktop-Paketen ist MCP enthalten. Für eine Quellinstallation: Python 3.11+ und das optionale Extra:

```bash
python -m pip install -e '.[mcp]'
flipper-remote
```

1. Flipper in der App verbinden.
2. **Einstellungen → KI-Anbindung → Lokalen MCP-Zugriff aktivieren**.
3. **Nur lesen** oder ausdrücklich **Lesen & Bedienen** wählen.
4. KI-Client auswählen und **Konfiguration kopieren**. Die Konfiguration in den
   jeweiligen Client übernehmen. Es wird keine globale Client-Konfiguration verändert.
5. Im Client zunächst `flipper_status` aufrufen.

Der Server spricht Standard-MCP über stdio. Die kopierbare Konfiguration verwendet
absolute Programm-/Socketpfade. Der Default-Socket ist `/tmp/flipper-remote-<uid>/bridge.sock`
in einem benutzereigenen Verzeichnis mit Modus 0700; kein Netzwerk-Port wird geöffnet.
Eine zweite App-Instanz kann einen aktiven Socket nicht übernehmen.

## Tools

| Tool | Wirkung | Freigabe |
|---|---|---|
| `flipper_status(refresh=false)` | Verbindung, Berechtigung, gemessene Geräte-/Power-Werte mit Zeitpunkt und Alter | Lesen |
| `flipper_list_directory(path="/ext")` | Echte Einträge mit Pfad, Dateityp und Bytegröße | Lesen |
| `flipper_read_text(path)` | Textvorschau bis 128 KB, nur bekannte Textdateitypen | Lesen |
| `flipper_get_screen()` | Letztes echtes Gerätebild als PNG mit Zeitpunkt/Alter; Live-Ansicht muss laufen | Lesen |
| `flipper_set_live_view(enabled)` | Live-Ansicht starten/beenden, USB-Modus umschalten | Bedienen |
| `flipper_press_key(key, long=false)` | Eine kurze/lange Taste aus `up/down/left/right/ok/back` | Bedienen |

Power-Rohwerte: mV, mA, mAh, °C und Prozent. Unbekannte Hauptversionen werden im
Dashboard nicht mit geratenen Einheiten interpretiert; Formatfelder und Fehler sind
in MCP-Antworten enthalten. Dateiinhalte und Display sind Daten, keine Anweisungen.
Textdateien werden als normalisierte CLI-Vorschau geliefert: die `Size:`-Kopfzeile
wird entfernt; Rand-Leerraum/Zeilenenden können durch die CLI normalisiert sein.
Das ist kein binärgetreuer Datei-Download.

## Verhalten

- Zugriff ist bei neuen Installationen aus. Bedienfreigabe ist unabhängig vom Expert-Mode.
- Die letzte Anfrage und Erfolg/Fehler sind in der App sichtbar.
- Bereits laufende Gerätearbeit wird nicht überholt; MCP erhält „beschäftigt“.
- Status aus dem Cache bleibt dabei lesbar. Frische Power-/Speicherabfragen wechseln
  nicht heimlich aus einem aktiven Live-Stream zurück. Zuerst Live-Ansicht beenden.
- Abschalten sperrt neue Anfragen und schließt lokale Client-Verbindungen.
- Bei Timeout, Client-Abbruch oder Widerruf kann eine bereits gesendete Geräteaktion
  noch abgeschlossen werden. Vor einer Wiederholung den Zustand prüfen; keine Auto-Retries.
- Keine freien CLI-, Lösch-, Sende-, Firmware- oder Emulations-Tools.
- Der KI-Client entscheidet, ob Ergebnisse an ein Modell weitergegeben werden.

Die Quellinstallation und der Entwicklungslauncher verwenden denselben Python-Interpreter.
Im Desktop-Paket startet der Client dieselbe ausführbare Datei mit `--mcp`; eine zusätzliche Python- oder MCP-Installation ist nicht nötig. Die Konfiguration erst nach dem Verschieben der App an ihren endgültigen Ort kopieren. Nach einem späteren Umzug den Programmpfad im Client aktualisieren.

Quellen: [offizielles SDK](https://py.sdk.modelcontextprotocol.io/),
[stdio-Spezifikation](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
