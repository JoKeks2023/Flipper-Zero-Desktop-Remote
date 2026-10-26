# Lokale Daten

| Plattform | Verzeichnis |
|---|---|
| macOS | `~/Library/Application Support/Flipper Zero Desktop Remote/` |
| Linux | `$XDG_CONFIG_HOME/flipper-zero-desktop-remote/` oder `~/.config/flipper-zero-desktop-remote/` |

`settings.json`: `last_port`, `theme` (`system`, `light`, `dark`), `start_module`,
`expert_mode` (Boolean), `easy_mode` (Boolean), `auto_connect` (Boolean),
`dashboard_refresh_seconds` (`0`, `5`, `10`, `30`), `mcp_enabled` und `mcp_control`
(Booleans, jeweils standardmäßig aus). `0` bedeutet manuelle Aktualisierung.
Auto-Connect ist ebenfalls standardmäßig aus und verwendet nur den zuletzt gespeicherten,
tatsächlich gefundenen Port. Vorhandene Einstellungen und Makros
werden weiter gelesen; die alten Optionen `accent`/`density` werden erhalten,
aber von der nativen Oberfläche nicht mehr ausgewertet.

`macros.json`: Objekt von Namen zu Listen mit CLI-Befehlen. Leere Makrolisten
bleiben nach Neustart leer. Ohne Expert-Mode sind nur lesende Abfragen und
Remote-Eingaben erlaubt; freie Makros benötigen Expert-Mode und Bestätigung.
Die Befehle können auf dem Gerät Änderungen ausführen. Ein Fehler stoppt die Sequenz.

Speicherung erfolgt über eine temporäre Datei mit anschließendem atomarem Austausch.
Ungültiges JSON fällt beim Laden auf Defaults zurück; die Originaldatei wird dabei
nicht überschrieben. Schreibfehler werden in der App angezeigt.

Die vier Einstellungsbereiche sind **Allgemein**, **Gerät**, **KI-Anbindung** und
**Über**. Änderungen werden sofort gespeichert. Easy Mode startet mit der Übersicht;
die Startseitenwahl für Alle Werkzeuge bleibt gespeichert. Die kopierbare Diagnose
enthält App-/Systemversionen und Verbindungszustände, keine Gerätekennung oder Dateiinhalte.
