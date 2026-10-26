# T-0001 — Benutzbare native Desktop-App

Auftrag: bestehendes Projekt benutzbar machen. Präzisierung am 26.10.2026:
Flet ersetzen, macOS UND Linux, Oberfläche ohne WebView.

Entscheidung: Qt Widgets über PySide6-Essentials. Kein Qt WebEngine, kein Flet,
kein Tauri. Python-Gerätekommunikation wiederverwenden.
GitHub: https://github.com/JoKeks2023/Flipper-Zero-Desktop-Remote/issues/2

Weitere Präzisierung: ansprechende UI, Easy Mode, Mac als Control Center;
Flipper übernimmt Hardware. Live-Display und Input als Zugang zu Geräte-Menüs,
Bibliotheken als eigene Desktop-Workflows. Easy Mode und Expert-Mode bleiben getrennt.
