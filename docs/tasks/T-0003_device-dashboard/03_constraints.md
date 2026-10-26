# Grenzen und Quellen

- Native Qt-Widgets für macOS/Linux, keine neuen Abhängigkeiten.
- Kompakte, sachliche Gestaltung aus T-0002 erhalten; helle/dunkle Tokens verwenden.
- Nur lesende Abfragen; keine Änderung von Ladestrom, Ladeschluss oder Versorgung.
- Power-Format 2 und Diagnose-Format 1 interpretieren; unbekannte Hauptversionen
  bleiben als Rohdaten einsehbar, erhalten aber keine geratenen Einheiten.
- Quelle für Einheiten und Ladezustände:
  [Power HAL](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/f7/furi_hal/furi_hal_power.c)
  und [Power HAL API](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/furi_hal_include/furi_hal_power.h).
- Konkrete Befehle/Schema auf dem angeschlossenen Momentum mntm-012 gelesen.
- Polling nur auf sichtbarer Startseite und bei freier CLI. Im Live-Modus werden
  Zeitpunkt und pausierte Aktualisierung angezeigt, ohne den Stream umzuschalten.
- Keine Gerätekennungen oder vollständigen Rohdaten in diese Berichte übernehmen.
