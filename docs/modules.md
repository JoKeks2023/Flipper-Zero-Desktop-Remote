# Module und tatsächlicher Funktionsumfang

| Bereich | Umsetzung |
|---|---|
| Control Center | Aufgaben-Karten und Gerätestatus |
| System | Geräteinfo, Loader-Status, normaler Neustart nach Bestätigung |
| Remote | Live-Display per RPC, Tasten kurz/lang, Rückkehr zur CLI für Dateiaktionen |
| Storage | Verzeichnisnavigation, Textvorschau, Ordner erstellen, bestätigtes Löschen |
| Infrared | `.ir`-Bibliothek, Vorschau, Öffnen in Infrared und Live-Bedienung |
| NFC/RFID | `.nfc`-Bibliothek, Vorschau, Öffnen in NFC; separate RFID-Desktopmaske noch nicht implementiert |
| Sub-GHz | `.sub`-Bibliothek, Vorschau, Öffnen in Sub-GHz und Live-Bedienung |
| BadUSB | `.txt`-Bibliothek, Vorschau, Öffnen in Momentum Bad KB nach Bestätigung |
| Makros | lokale CLI-Sequenzen, Speicherung, Abbruch und Fehleranzeige |
| Einstellungen | Darstellung, Startmodul, Expert-Mode; Easy Mode oben |

Nicht als eigene Desktopaktionen implementiert: direkte IR-Dateisendefunktion,
NFC-Lesen/Schreiben/Emulieren und Sub-GHz-Empfangskonfiguration. Diese Geräte-Menüs
werden über die Live-Fernbedienung bedient, soweit die Firmware sie im RPC-Modus erlaubt.
Keine vollständige Funktionsparität für jede Momentum-App nachgewiesen.

Belegte Schnittstellen: Gerätehilfe von Momentum mntm-012, sowie
[offizielle Protobuf-GUI](https://github.com/flipperdevices/flipperzero-protobuf/blob/dev/gui.proto)
und [Momentum Loader](https://github.com/Next-Flip/Momentum-Firmware/blob/mntm-012/applications/services/loader/loader_cli.c).
Der alte Befehl `ir tx <Dateipfad>` war ungültig und wurde entfernt. Es gibt auf dem
geprüften Gerät keinen allgemeinen `badusb run`-CLI-Befehl.
