# Mitwirken

Beiträge zu **Flipper Zero Desktop Remote** sind willkommen – egal ob Bugfixes, neue Features oder Verbesserungen der Dokumentation.

---

## Inhaltsverzeichnis

- [Entwicklungsumgebung einrichten](#entwicklungsumgebung-einrichten)
- [Projektstruktur verstehen](#projektstruktur-verstehen)
- [Änderungen vornehmen](#änderungen-vornehmen)
- [Code-Stil](#code-stil)
- [Pull Request einreichen](#pull-request-einreichen)
- [Fehler melden](#fehler-melden)

---

## Entwicklungsumgebung einrichten

### 1. Repository forken und klonen

```bash
# Repository forken (über GitHub UI), dann klonen:
git clone https://github.com/<dein-username>/Flipper-Zero-Desktop-Remote.git
cd Flipper-Zero-Desktop-Remote

# Upstream-Remote hinzufügen:
git remote add upstream https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote.git
```

### 2. Virtuelle Umgebung einrichten

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
```

### 3. App starten

```bash
python src/main.py
```

### 4. Upstream-Änderungen einholen

```bash
git fetch upstream
git merge upstream/main
```

---

## Projektstruktur verstehen

```text
src/
├── main.py                   # Einstiegspunkt – startet Flet
├── core/
│   ├── capabilities.py       # Feature-Flags & Expert-Mode-Logik
│   ├── connection_manager.py # Port-Scan (macOS / Linux)
│   ├── serial_client.py      # Serial-Verbindung, Reader-Thread, Log-Queue
│   └── flipper_api.py        # Flipper-CLI-Befehle als Python-Methoden
├── persistence/
│   ├── paths.py              # Plattformkonforme Konfigurationspfade
│   └── config_store.py       # Laden/Speichern von settings.json und macros.json
└── ui/
    └── app.py                # Gesamte Flet-UI (alle Tabs und Logik)
```

| Modul | Verantwortlichkeit |
|---|---|
| `core/serial_client.py` | Low-Level-Serial: Verbinden, Lesen (Thread), Schreiben, Log-Queue |
| `core/flipper_api.py` | High-Level-API: Kapselt Befehle als Python-Methoden |
| `core/connection_manager.py` | Port-Erkennung: filtert Ports nach Plattform und Hersteller |
| `core/capabilities.py` | Feature-Flags: steuert, welche Tabs aktiv/gesperrt sind |
| `persistence/config_store.py` | JSON-Persistenz für Einstellungen und Makros |
| `ui/app.py` | Komplette UI: alle Tabs, Event-Handler, Theme-Logik |

---

## Änderungen vornehmen

### Feature-Branch erstellen

```bash
git checkout -b feature/mein-feature
# oder für Bugfixes:
git checkout -b fix/beschreibung-des-bugs
```

### Änderungen committen

```bash
git add .
git commit -m "feat: kurze beschreibung der änderung"
```

Empfohlene Commit-Prefixe (Conventional Commits):

| Prefix | Verwendung |
|---|---|
| `feat:` | Neue Funktion |
| `fix:` | Bugfix |
| `docs:` | Nur Dokumentation |
| `refactor:` | Code-Umstrukturierung ohne Funktionsänderung |
| `chore:` | Build-System, Dependencies, sonstige Wartungsaufgaben |

---

## Code-Stil

Das Projekt verwendet Python 3.10+ mit folgenden Konventionen:

- **Type Hints:** Alle öffentlichen Funktionen und Methoden sollten Typ-Annotierungen haben.
- **`from __future__ import annotations`:** In allen Modulen, die Type Hints verwenden.
- **Dataclasses:** Für einfache Datenstrukturen (`@dataclass(frozen=True)` für unveränderliche Werte).
- **Keine globalen Zustandsänderungen:** State wird in `run()` lokal gehalten und über Closures weitergegeben.
- **Abhängigkeiten:** Nur bestehende Abhängigkeiten (`flet`, `flet-desktop`, `pyserial`). Neue Abhängigkeiten erst nach Absprache hinzufügen.

### Empfohlene Werkzeuge

```bash
# Linting
pip install ruff
ruff check src/

# Formatierung
pip install black
black src/

# Type-Checking
pip install mypy
mypy src/
```

---

## Pull Request einreichen

1. Branch auf deinen Fork pushen:
   ```bash
   git push origin feature/mein-feature
   ```
2. Auf GitHub einen Pull Request gegen den `main`-Branch öffnen.
3. Im PR-Titel und der Beschreibung erklären, was geändert wurde und warum.
4. Auf Feedback reagieren und ggf. Änderungen vornehmen.

### Checkliste vor dem PR

- [ ] Code läuft ohne Fehler (`python src/main.py`)
- [ ] Keine neuen unbeabsichtigten Abhängigkeiten
- [ ] Dokumentation aktualisiert (falls nötig)
- [ ] Commit-Messages folgen den Konventionen

---

## Fehler melden

Fehler und Verbesserungsvorschläge bitte als [GitHub Issue](https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/issues) einreichen.

**Hilfreiche Informationen im Issue:**

- Betriebssystem und Version
- Python-Version (`python3 --version`)
- Flipper Zero Firmware-Version
- Fehlermeldung (vollständiger Traceback)
- Schritte zum Reproduzieren
