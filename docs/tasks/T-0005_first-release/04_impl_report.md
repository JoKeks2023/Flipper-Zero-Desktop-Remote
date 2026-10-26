# Umsetzung

- `src/ui/theme.py`: neutralere Flächen, ruhigere Aktionen, Reiter mit Unterstreichung, sichtbare Checkboxen in beiden Themes.
- `src/ui/settings_page.py`: begrenzte Inhalts-/Feldbreiten, kompakte Credits-Tabelle; Navigation zeigt & als Text.
- `src/ui/assets/`, `packaging/create_icons.py`: eigenes Vektorsymbol mit PNG/ICNS-Ableitungen.
- `src/main.py`, `ui/mcp_panel.py`: eingefrorene App startet ihren eigenen mitgelieferten stdio-MCP über `--mcp`; keine separate Installation nötig.
- `.github/workflows/packages.yml`: drei Zielpakete, Regression und tatsächliche GUI-/MCP-Paketstarts; Qt-Notices und Versionsinventar in jedem Paket.
- `README.md`, `docs/images/`: neuer Repository-Auftritt mit echten Screenshots, direkter Download-Auswahl und Vorschau-Grenzen.
- Installation, Build, MCP und dynamische Bibliotheksquellen dokumentiert; `CHANGELOG.md` ergänzt.

Zusätzliche Behavior-Änderung für die Veröffentlichung: Standalone-Pakete enthalten MCP selbst. Der Entwicklercheck `--smoke-test` verwendet temporäre Einstellungen und keine Hardware. Im normalen Gerätebetrieb wurden keine neuen Aktionen ergänzt.
