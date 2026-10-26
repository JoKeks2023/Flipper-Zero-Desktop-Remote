# Verifikation — 26.10.2026

## Laufende macOS-App und echtes Momentum-Gerät

- Neue Oberfläche tatsächlich gestartet, Gerät verbunden. Einstellungsbereiche
  und Über-Seite visuell geprüft. MIT- und Abhängigkeiten-Tab im Lizenzdialog geöffnet.
- MCP im Lesemodus aktiviert. Standard-Clientprozess des offiziellen SDKs mit
  klassischer MCP-Initialisierung/stdio: alle sechs Tools erkannt.
- Frischer Status: verbunden, 98 % Akku und echte Power-Daten.
- IR-Verzeichnis mit 16 Einträgen gelesen; bekannte `Canon RC-6.ir` mit 131 Bytes
  gelesen. Nach Formatkorrektur beginnt die Vorschau mit `Filetype: IR signals file`.
- Bedienung im Lesemodus als MCP-Fehler zurückgewiesen; kein Tastendruck gesendet.
- Bei in der UI gestarteter Live-Ansicht echten MCP-Bildinhalt empfangen:
  `image/png`, 128×64 Pixel; empfangenes Bild tatsächlich betrachtet.
- Nach ausdrücklicher Nutzerfreigabe „Bedienung für diesen Test freigeben“:
  Live-Ansicht über MCP gestartet, aktuelles Bild empfangen, genau ein kurzer
  `back`-Tastendruck am vorher betrachteten Startbildschirm bestätigt,
  Live-Ansicht über MCP beendet und anschließend frische CLI-/Dateidaten gelesen.
- Danach per UI wieder „Nur lesen“ eingestellt und sichtbaren Status geprüft.
- UI-Aktivität zeigt echte Anfragen mit Erfolg/Fehler. Kein zweiter USB-Prozess nötig.

## Automatisiert und Paketierung

- 43 Regressionstests grün: CLI/RPC, Speicherung, Dashboard, Qt-Worker sowie neue
  MCP-Verbindung, Berechtigungen/Widerruf, Busy-Zustände, Pfad-/Größenprüfung,
  PNG, exklusive Socket-Besitzersperre und echter stdio-Clientprozess.
- Neue Einstellungsprüfungen: Intervall/Timer und manuell, Modussynchronisierung,
  gespeicherte Startseite, nur letzter Port bei Auto-Connect, begrenzte Diagnose.
- Kleines reines Python-Wheel erfolgreich gebaut. ZIP-Inhalt geprüft: MCP-Server,
  Settings-Modul, beide UI-Lizenzressourcen, MIT-Metadaten und MCP-Extra enthalten.
- Quellcode geparst, `git diff --check` ohne Befund.
- Socket-Tests benötigen auf diesem Host die Freigabe außerhalb der Sandbox,
  weil das Anlegen privater Unix-Sockets innerhalb der Sandbox gesperrt ist.

## Grenzen

- Tatsächliche Geräte-/Sichtprüfung macOS, dunkle Darstellung; Linux und helle
  Darstellung hier nicht separat visuell abgenommen.
- Keine vollständige Installation in einem fremden KI-Host vorgenommen. Es wurde
  dessen Standardprotokoll mit einem echten MCP-SDK-Clientprozess geprüft.
- Signierte/notarisierte Desktop-Pakete, sauberer Zielrechner und vollständige
  Notices aller tatsächlich gebündelten Binärkomponenten bleiben vor Binary-Release offen.
- Der MCP-Server ist eine optionale Python-Installation, kein eigenständiges Binary.
- Keine Sende-, Emulations-, Firmware- oder BadUSB-Aktion getestet.
