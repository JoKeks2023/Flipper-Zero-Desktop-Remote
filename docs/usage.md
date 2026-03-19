# Benutzung

Diese Seite erklärt die Benutzeroberfläche und typische Workflows in **Flipper Zero Desktop Remote**.

---

## Inhaltsverzeichnis

- [Oberfläche im Überblick](#oberfläche-im-überblick)
- [Verbindung aufbauen](#verbindung-aufbauen)
- [Modul-Tab wechseln](#modul-tab-wechseln)
- [Log-Konsole](#log-konsole)
- [Einstellungen](#einstellungen)
- [Expert-Mode aktivieren](#expert-mode-aktivieren)
- [Typische Workflows](#typische-workflows)

---

## Oberfläche im Überblick

```
┌─────────────────────────────────────────────────────────────────┐
│  Flipper Zero Desktop Remote                                    │
│  Steuere Flipper-Module am Desktop über klare Aktionen          │
├─────────────────────────────────────────────────────────────────┤
│  Port: [/dev/cu.usbmodem... ▼]  [Scan]  [Connect]  [Disconnect]│
├────────┬────────────────────────────────────────────────────────┤
│        │                                                        │
│ System │   ┌── Modul-Inhalt ──────────────────────────────┐    │
│ Remote │   │                                              │    │
│ Storage│   │  Hier erscheinen die Aktions-Buttons und     │    │
│Infrared│   │  Steuerelemente des gewählten Moduls.        │    │
│NFC/RFID│   │                                              │    │
│Sub-GHz │   └──────────────────────────────────────────────┘    │
│ BadUSB │                                                        │
│ Makros │   ┌── Log-Konsole ───────────────────────────────┐    │
│        │   │  [INFO] Connected to /dev/cu.usbmodem...     │    │
│        │   │  > device_info                               │    │
│        │   │  hw_ver: ...                                 │    │
└────────┴───┴──────────────────────────────────────────────┘────┘
```

Die Oberfläche ist in drei Bereiche gegliedert:

1. **Verbindungsleiste** (oben) – Port-Auswahl, Scan, Connect/Disconnect
2. **Modul-Tabs** (links) – Navigation zwischen den 8 Funktionsbereichen
3. **Inhaltsbereich** (rechts) – Aktions-Buttons und Log-Konsole des aktiven Moduls

---

## Verbindung aufbauen

1. Flipper Zero per USB verbinden.
2. Auf **Scan** klicken – die Dropdown-Liste füllt sich mit erkannten Ports.
3. Port in der Liste auswählen (z. B. `/dev/cu.usbmodem14301`).
4. **Connect** klicken.
5. Erfolgreiche Verbindung wird in der Log-Konsole bestätigt.

Um die Verbindung zu trennen: **Disconnect** klicken oder die App schließen.

> Der zuletzt verwendete Port wird automatisch gespeichert und beim nächsten Start vorausgewählt.

---

## Modul-Tab wechseln

Klicke links auf einen der acht Modul-Tabs:

| Tab | Zugang |
|---|---|
| System | Immer verfügbar |
| Remote | Immer verfügbar |
| Storage | Immer verfügbar |
| Infrared | Immer verfügbar |
| NFC/RFID | Nur im Expert-Mode |
| Sub-GHz | Nur im Expert-Mode |
| BadUSB | Nur im Expert-Mode |
| Makros | Immer verfügbar |

Gesperrte Tabs (NFC/RFID, Sub-GHz, BadUSB) zeigen einen Hinweis und einen Link zu den Einstellungen, wenn der Expert-Mode inaktiv ist.

> Detaillierte Beschreibung aller Module: [modules.md](modules.md)

---

## Log-Konsole

Die Log-Konsole am unteren Rand des Inhaltsbereichs zeigt:

- **`[INFO]`** – Verbindungsstatus und App-Meldungen
- **`[WARN]`** / **`[ERROR]`** – Warnungen und Fehler
- **`> Befehl`** – Gesendete Befehle (mit vorangestelltem `>`)
- **Geräteantworten** – Rohdaten vom Flipper Zero

Der Puffer hält bis zu **2.000 Zeilen**. Ältere Zeilen werden automatisch entfernt. Der Stream wird kontinuierlich aktualisiert, solange eine Verbindung besteht.

---

## Einstellungen

Die Einstellungen sind über den **Einstellungen**-Tab (⚙) erreichbar. Folgende Optionen stehen zur Verfügung:

| Einstellung | Beschreibung | Standard |
|---|---|---|
| **Theme** | `dark` oder `light` | `dark` |
| **Akzentfarbe** | `orange`, `amber`, `red` | `orange` |
| **Dichte** | `comfort` (größere Abstände) oder `compact` | `comfort` |
| **Startmodul** | Welcher Tab beim Start aktiv ist | `System` |
| **Expert-Mode** | Schaltet gesperrte Module frei | `aus` |

Änderungen werden sofort gespeichert.

---

## Expert-Mode aktivieren

> ⚠️ Den Expert-Mode **nur in kontrollierten und rechtlich zulässigen Umgebungen** aktivieren.

1. Einstellungen öffnen (⚙-Tab oder Einstellungen-Button).
2. Den Schalter **Expert-Mode** auf `an` stellen.
3. Die Tabs NFC/RFID, Sub-GHz und BadUSB werden sofort entsperrt.

Deaktivierung erfolgt auf dem gleichen Weg. Der Status wird persistent gespeichert.

---

## Typische Workflows

### Geräteinformationen abrufen

1. Tab **System** öffnen.
2. Button **Device Info** klicken.
3. Antwort in der Log-Konsole lesen.

### Flipper Zero navigieren (Remote)

1. Tab **Remote** öffnen.
2. Mit den Pfeiltasten (↑ ↓ ← →) navigieren, **OK** bestätigen, **Back** zurückgehen.
3. Für Long-Press: Taste gedrückt halten (Button bleibt aktiv) oder den **Long**-Button nutzen.

### Storage-Inhalte anzeigen

1. Tab **Storage** öffnen.
2. Pfad eingeben (Standard: `/`) und **List** klicken.
3. Verzeichnisinhalt erscheint in der Log-Konsole.

### Makro erstellen und ausführen

1. Tab **Makros** öffnen.
2. Makro-Namen eingeben, Befehle zeilenweise eingeben.
3. **Speichern** klicken.
4. Makro in der Liste auswählen und **Ausführen** klicken.

> Mehr zu Makros: [configuration.md](configuration.md)
