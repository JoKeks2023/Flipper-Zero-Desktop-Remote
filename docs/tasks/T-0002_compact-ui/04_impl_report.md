# Umsetzung — 26.10.2026

- Fensterstruktur neu: 196 px Seitenleiste mit gruppierten Zielen, kleine Geräteleiste,
  Hauptarbeitsfläche. Mode-Select im Seitenleistenfuß statt in einer großen Kopfleiste.
- Kompakte Typografie: 19 px Titel, 12–13 px Bedienelemente, 11 px Metadaten.
- Bisherige Plattform-Cliparts durch einheitliche Qt-Vektorsymbole ersetzt.
- Startseite: sechs 44 px hohe Werkzeugzeilen statt eines Rasters aus großen Karten.
- Gemeinsame semantische Farben und Zustände für helle/dunkle Darstellung in theme.py.
- Standard-Buttons vollständig vereinheitlicht; Haupt-, Neben- und Löschaktionen visuell getrennt.
- Live-Display begrenzt auf 256 px Höhe; Pixelbild in ganzzahligen Stufen bis 4×.
  Bildschirmfarbe bewusst von kräftigem Orange auf gedämpftes Amber geändert.
- Remote-Tasten kompakter, Tastaturbedienung bleibt erhalten.
- Dateien: dichte Zweispaltenliste mit Größenausrichtung und Vorschau nebeneinander,
  Monospace für Vorschau/Pfade/Zahlen; eindeutige Ordner- und Dateisymbole.
- Selects besitzen einen explizit gezeichneten Auswahlpfeil; Toolbar-Icons mit Tooltips.
- Erfolgsmeldungen von Datei-/Geräteaktionen verwenden verständliche Aktionsnamen.

Kein Transport- oder Firmwareprotokoll geändert. Keine neuen Abhängigkeiten.
Easy-/Expert-Mode und Geräteaktionen sind funktional erhalten.
