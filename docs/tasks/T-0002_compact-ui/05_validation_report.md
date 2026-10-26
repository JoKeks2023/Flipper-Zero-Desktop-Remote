# Verifikation — 26.10.2026

## Laufende macOS-App

- Neu gestartet, native Qt-App tatsächlich geöffnet.
- Startseite/Seitenleiste visuell geprüft: kompakte Liste und konsistente Glyphen.
- Verbinden: Momentum-Gerät erkannt, Name und grüner Punkt mit Status sichtbar.
- Werkzeugzeile „Live-Bedienung“ öffnet die Remote-Seite per Accessibility-Aktion.
- Live-Ansicht gestartet: echtes Flipper-Display sichtbar, kleine Tasten daneben,
  Displaydarstellung begrenzt und pixelgenau skaliert.
- Von Live zu IR-Bibliothek gewechselt: automatische RPC/CLI-Umschaltung weiter funktionsfähig.
- `/ext/infrared`: 15 Einträge im Browser, Name und Größe nebeneinander, Vorschau rechts.
- Per Tastatur `Canon RC-6.ir` gewählt und „Inhalt anzeigen“ geklickt:
  131 Bytes und tatsächlicher Dateiinhalt gleichzeitig mit der Liste sichtbar.
  Statusmeldung: „Abgeschlossen: Dateivorschau laden“.

## Automatisiert

23 vorhandene Regressionstests grün, einschließlich Navigation per Accessibility-
Toggle, Qt-Worker, Tastatur-Remote, Browser/Vorschau, Easy Mode und Protokolltests.
Quellcode kompiliert; `git diff --check` ohne Befund.

## Grenzen

Die tatsächliche visuelle Prüfung betraf Übersicht, Live-Bedienung und Dateibrowser
in der dunklen Darstellung auf macOS. Helle Darstellung wird weiterhin implementiert,
aber ist in diesem Durchlauf nicht separat visuell abgenommen. Linux-/Release-Paket-
Abnahme aus T-0001 bleibt offen. Keine Sende-/Emulationsfunktionen zum Testen ausgeführt.
