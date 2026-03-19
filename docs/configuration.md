# Konfiguration

Diese Seite beschreibt alle persistenten Einstellungen und Dateien von **Flipper Zero Desktop Remote**.

---

## Inhaltsverzeichnis

- [Speicherorte](#speicherorte)
- [settings.json](#settingsjson)
- [macros.json](#macrosjson)
- [Einstellungen zurücksetzen](#einstellungen-zurücksetzen)
- [Makros manuell bearbeiten](#makros-manuell-bearbeiten)

---

## Speicherorte

Die App speichert alle Konfigurationsdateien plattformkonform:

| Betriebssystem | Pfad |
|---|---|
| **macOS** | `~/Library/Application Support/Flipper Zero Desktop Remote/` |
| **Linux** | `$XDG_CONFIG_HOME/flipper-zero-desktop-remote/` oder `~/.config/flipper-zero-desktop-remote/` |

Die Verzeichnisse werden beim ersten Start automatisch angelegt.

---

## settings.json

Die Datei `settings.json` speichert die App-Einstellungen. Sie wird beim Start geladen und bei jeder Änderung sofort geschrieben.

### Standardinhalt

```json
{
  "last_port": "",
  "expert_mode": false,
  "theme": "dark",
  "accent": "orange",
  "density": "comfort",
  "start_module": "System"
}
```

### Felder

| Schlüssel | Typ | Mögliche Werte | Beschreibung |
|---|---|---|---|
| `last_port` | String | Portpfad, z. B. `/dev/cu.usbmodem14301` | Zuletzt verwendeter Serial-Port |
| `expert_mode` | Boolean | `true` / `false` | Expert-Mode aktiv (schaltet NFC/RFID, Sub-GHz, BadUSB frei) |
| `theme` | String | `"dark"` / `"light"` | App-Theme |
| `accent` | String | `"orange"` / `"amber"` / `"red"` | Akzentfarbe der UI |
| `density` | String | `"comfort"` / `"compact"` | UI-Dichte (Abstände und Schaltflächenhöhe) |
| `start_module` | String | `"System"` / `"Remote"` / `"Storage"` / … | Aktiver Tab beim Start |

---

## macros.json

Die Datei `macros.json` speichert alle benutzerdefinierten Makros. Ein Makro ist eine benannte Liste von Flipper-CLI-Befehlen, die sequenziell gesendet werden.

### Standardinhalt

```json
{
  "Status": [
    "device_info",
    "storage list /"
  ],
  "Quick Reboot": [
    "power reboot"
  ]
}
```

### Format

```json
{
  "Makro-Name": [
    "befehl1",
    "befehl2",
    "..."
  ]
}
```

- **Makro-Name:** Beliebiger String, darf Leerzeichen enthalten.
- **Befehle:** Jede Zeile entspricht einem Flipper-CLI-Befehl (wie er auch direkt in die Konsole eingegeben werden würde).
- Leere Zeilen werden beim Laden ignoriert.
- Ungültige Einträge (falsche Typen) werden beim Laden gefiltert.

### Beispiel mit allen Modul-Typen

```json
{
  "System-Check": [
    "device_info",
    "storage list /"
  ],
  "Vibro-Test": [
    "vibro 1",
    "vibro 0"
  ],
  "Navigation-Demo": [
    "input send up short",
    "input send down short",
    "input send ok short",
    "input send back short"
  ],
  "Reboot-Sequenz": [
    "power reboot"
  ]
}
```

---

## Einstellungen zurücksetzen

Um alle Einstellungen auf die Standardwerte zurückzusetzen, die `settings.json` löschen:

```bash
# macOS
rm ~/Library/Application\ Support/Flipper\ Zero\ Desktop\ Remote/settings.json

# Linux
rm ~/.config/flipper-zero-desktop-remote/settings.json
```

Beim nächsten Start werden die Standardwerte verwendet und eine neue `settings.json` angelegt.

---

## Makros manuell bearbeiten

Die `macros.json` kann mit jedem Texteditor direkt bearbeitet werden. Die App lädt die Datei beim Start sowie über den **Laden**-Button im Makros-Tab neu.

Pfad öffnen:

```bash
# macOS
open ~/Library/Application\ Support/Flipper\ Zero\ Desktop\ Remote/

# Linux
xdg-open ~/.config/flipper-zero-desktop-remote/
```

> **Tipp:** Beim manuellen Bearbeiten auf gültiges JSON achten. Fehler in der Datei führen dazu, dass die Standardmakros geladen werden.
