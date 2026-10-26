# Benutzung

1. Flipper per USB verbinden, qFlipper schließen, **Verbinden** klicken.
2. Die **Übersicht / Control Center** zeigt aktuelle Geräte-, Akku- und Power-Daten.
   Darunter die gewünschte Aufgabe auswählen.
3. **Flipper bedienen → Live-Ansicht starten** zeigt das echte Geräte-Display.
   Die Pfeile, OK und Zurück bedienen die Geräte-Menüs. Für langes Drücken den
   entsprechenden Schalter aktivieren. Pfeiltasten, Enter und Escape/Backspace
   funktionieren bei Fokus auf der Remote-Seite ebenfalls. Es werden keine simulierten Gerätebilder gezeigt.
4. **Dateien** oder eine Modulbibliothek öffnen. Das Programm wechselt bei Bedarf
   von Display-RPC zurück zur CLI und lädt den aktuellen Ordner.

## Geräte-Dashboard

Die Startseite liest den Gerätestatus beim Verbinden und bei Rückkehr zur Übersicht.
Solange sie sichtbar ist, werden die Messwerte bei freier Verbindung alle 10 Sekunden
neu abgefragt (unter Einstellungen auf 5/10/30 Sekunden oder manuell änderbar).
**Aktualisieren** liest sie sofort erneut; der Zeitpunkt steht unter
den Werten. **Alle Geräteinfos…** öffnet eine Momentaufnahme aller gemeldeten Rohwerte
in den Bereichen Gerät, Akku & Strom und Power-Diagnose.

Während einer laufenden Live-Ansicht bleibt der letzte Messzeitpunkt sichtbar und
die Aktualisierung pausiert. Zum Fortsetzen die Live-Ansicht beenden. Fehlende Werte
erscheinen als **—**, fehlgeschlagene Abfragen werden benannt. **Lädt nicht** ist der
vom Flipper gemeldete Ladezustand und kann auch bei angeschlossenem USB auftreten.

## Easy Mode und alle Werkzeuge

Die Auswahl oben wechselt zwischen **Easy Mode** und **Alle Werkzeuge**.
Easy Mode blendet Portdetails (außer bei mehreren Geräten), Systemdetails,
freie Makros und das technische Protokoll aus. Expert-Mode wird dadurch nicht aktiviert.
**Alle Werkzeuge** zeigt zusätzlich System und Makros. Unter Ansicht lässt sich das
technische Protokoll einblenden. Fehler erscheinen auch unten in der Statusleiste.

Unter **Einstellungen** sind Allgemein, Gerät, KI-Anbindung und Über getrennt.
Die automatische Verbindung zum letzten USB-Port ist optional. **Über** enthält
Credits, Lizenzhinweise und Links zum Projekt. MCP: [Einrichtung und Tools](mcp.md).

## Dateien

Ordner doppelklicken; **Übergeordnet** geht eine Ebene zurück. Der Ordner-Select
enthält Startpfade und bereits entdeckte Verzeichnisse. Dateien auswählen und
**Inhalt anzeigen** klicken. Die Vorschau ist auf 128 KB begrenzt und für Textdateien
gedacht, kein Binärdatei-Editor. Vor Löschen wird der genaue Gerätepfad bestätigt.
Ein neuer Ordnername ist echter Freitext; bekannte Pfade bleiben Auswahllisten.

## Geräte-Apps

Bei IR/NFC/Sub-GHz/BadUSB startet **Am Flipper öffnen** die passende Geräte-App
und öffnet danach die Live-Bedienung. Dafür ist Expert-Mode und eine Bestätigung
nötig. Geräte-App-Start ist firmwareabhängig; Fehler stehen im Protokoll.
Das Starten von BadUSB-Dateien kann bereits Tastatureingaben auslösen.

## Abbrechen und Trennen

Laufende CLI-Vorgänge können mit **Abbrechen** (Strg+C) unterbrochen werden.
Makros führen danach keine weiteren Schritte aus. **Trennen** beendet die
Verbindung und verwirft die Geräteanzeige. Schließen gibt den USB-Port frei.

**Gehe zu** enthält Modulziele mit Tastenkürzeln für die ersten neun Ziele.
Auf macOS entsprechen diese Command+1 bis Command+9, auf Linux Strg+1 bis Strg+9.
