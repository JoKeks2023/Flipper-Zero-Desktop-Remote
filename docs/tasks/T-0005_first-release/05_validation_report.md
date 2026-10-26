# Verifikation · 26.10.2026

## Lokal

- 43 Regressionstests nach UI-Politur grün; abschließender Durchlauf nach Paket-Einstieg folgt im selben Release-Gate.
- `--smoke-test`: zehn echte Qt-Seiten, zwei Themes, 960 px Mindestbreite, App-Symbol und beide Lizenztexte geladen.
- Entwicklungs-App über macOS-Fenster geöffnet, realen Flipper verbunden: Dashboard zeigt 98 %, 5,10 V und 21 °C; Aktualisierung beobachtet.
- Einstellungen/Theme-Wechsel sichtbar geklickt; Screenshots in `docs/images/` sind Originalaufnahmen der laufenden App. Keine UID/MAC oder Dateiinhalte veröffentlicht.
- MCP-Freigabe bleibt „Nur lesen“; bei dieser Abnahme keine Eingabe-/Sendeaktionen.

## Paket-CI

[Build 40399614117](https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/actions/runs/40399614117) von `8ad9406`: Linux x86_64 und macOS arm64 erfolgreich, Intel zum Zeitpunkt dieses Eintrags noch in Arbeit. Jeder Paketjob führt die 43 Tests und den echten Paket-Smoke aus (MCP-Handshake/sechs Tools/erwarteter Fehler ohne Desktop; Qt-Seiten/Themes/Lizenzen).

Die finale Paketrevision und die lokale Standalone-Abnahme werden vor Veröffentlichung nachgetragen.

## Offene Plattformgrenzen

- Keine Developer-ID-Signierung/Notarisierung; macOS-Start kann eine bewusste Ausnahme erfordern.
- Linux bisher ohne USB-Hardware; Intel bisher nur Paket-CI.
- macOS 14 ist die konfigurierte Untergrenze, keine gesonderte Installation auf macOS 14 geprüft.
- Keine Abnahme von Senden, Emulation oder BadUSB-Ausführung; Gerätequelle bislang Momentum mntm-012.
