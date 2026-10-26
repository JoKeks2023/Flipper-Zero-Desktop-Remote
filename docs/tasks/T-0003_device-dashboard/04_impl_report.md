# Umsetzung — 26.10.2026

- `core/device_status.py`: drei lesende Abfragen mit je 4 Sekunden Timeout,
  getrennten Fehlern und Zeitpunkt; Parser bewahrt Doppelpunkte in Werten.
- Optionale/fehlgeschlagene Power-Abfragen verhindern die Geräteverwendung nicht.
  Jede Antwort ersetzt die betreffende Datenquelle vollständig. Keine alten Werte
  als aktuelle Messung nach fehlgeschlagenem Refresh.
- Bekannte Formatversionen, endliche Zahlen und Prozentgrenzen geprüft;
  Null bleibt ein echter Messwert, fehlend/ungültig erscheint als Gedankenstrich.
- `ui/dashboard.py`: Gerätekopf, drei Messwertbereiche, zwei kompakte Detailspalten,
  expliziter Aktualisierungszeitpunkt und nativer Dialog mit drei Rohdaten-Tabs.
- Automatisch beim Verbinden, bei Rückkehr und alle 10 Sekunden auf der Übersicht,
  sofern CLI verbunden und kein Auftrag aktiv. Keine RPC/CLI-Umschaltung durch Polling.
- Während Live-RPC: Pause und letzter Messzeitpunkt sichtbar; Refresh gesperrt.
- Werkzeugzugänge unterhalb in zwei Spalten; bei kleinen Fenstern vertikal scrollbar.
  Größenverhalten der Werkzeugzeilen angepasst, damit keine horizontale Überbreite entsteht.
- Trennen löscht alle Werte. Qt-Worker, Easy Mode und bisherige Geräteaktionen erhalten.
- Einheiten: mV → V, mA, mAh, °C und Prozent gemäß Power HAL; USB-Spannung und
  Ladezustand getrennt dargestellt. Keine erfundene Laufzeit-/Leistungsschätzung.

Kein neuer Stack, keine neuen Abhängigkeiten, keine aktiven Hardwareaktionen.
