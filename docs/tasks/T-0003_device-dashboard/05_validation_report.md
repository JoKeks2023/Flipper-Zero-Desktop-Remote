# Verifikation — 26.10.2026

## Laufende macOS-App mit Momentum mntm-012

- App mehrfach tatsächlich neu gestartet und per USB verbunden.
- Direkte CLI-Abfragen mit Dashboard verglichen: 98 % Akku, Zustand `discharging`,
  3919 mV Akku, 0 mA, 20 °C, 100 % Gesundheit, 2056/2100 mAh;
  5100 mV USB und 3984 mV Systemspannung.
- Dashboard zeigt entsprechend 3,919 V / 5,10 V / 3,984 V und „Lädt nicht“.
- Firmware mntm-012, Builddatum, Hardware-Revision, Region und RPC 0.25 sichtbar.
- „Aktualisieren“ tatsächlich geklickt; neuer Zeitpunkt und erfolgreiche Statusmeldung.
  Spätere automatische Abfragen in der laufenden Oberfläche beobachtet.
- „Alle Geräteinfos“ geöffnet; Gerät-, Akku- und Power-Diagnose-Tabs angeklickt.
  Rohdaten stimmen mit den gelesenen Quellen überein. Dialog danach geschlossen.
- Von der Übersicht Live-Bedienung gestartet, bei laufendem Display zurückgekehrt:
  „Aktualisierung pausiert · Live-Ansicht aktiv · Letzte Messung …“ sichtbar,
  Refresh gesperrt, Verbindung bleibt aktiv.
- Abschließende kompakte Darstellung visuell geprüft: alle drei Messwertbereiche,
  beide Detailspalten und sechs Werkzeugzugänge im normalen Fenster gleichzeitig sichtbar.
- Start ohne Verbindung zeigt leere Werte und deaktivierte Abfrage/Details.
  Schließen während Verbindung/Live-Modus gibt USB für erneuten App-Start frei.

## Automatisiert

32 Tests grün (`unittest discover`), davon 9 neue Prüfungen:
Parser, unbekannte/ungültige Zahlen und Formate, echte Nullwerte, unabhängiger
Ladezustand, optionale Fehler, Abbruch, Refresh/Leeren, keine Wiederverwendung alter
Power-Werte sowie Polling-Sperren und Fenstergrößen.

Qt-Laufzeit bei 1080×680: keine horizontale/vertikale Überbreite. Bei 960×600:
kein horizontaler Überlauf, nötigenfalls vertikales Scrollen. Diese Größenprüfung
erfolgte im Offscreen-Qt-Test. `git diff --check` ohne Befund.

## Grenzen

- Physische Geräteprüfung und Sichtprüfung auf macOS in dunkler Darstellung.
- Helle Tokens sind implementiert; keine separate visuelle Abnahme in diesem Durchlauf.
- Linux-Geräteprüfung und eigenständige Release-Pakete weiterhin offen (T-0001).
- Abfragen sind aufeinanderfolgende Messungen, kein atomarer Snapshot aller Chips.
- Keine Sende-, Emulations-, BadUSB- oder Power-Konfigurationsaktionen ausgeführt.
