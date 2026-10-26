# Gebündelte Komponenten und Quellen

Der eigene Anwendungscode ist MIT-lizenziert. Die Desktop-Pakete enthalten außerdem Python, Qt/PySide6/Shiboken, pySerial, das MCP-SDK und dessen Abhängigkeiten unter deren jeweiligen Lizenzen. [Übersicht](../THIRD_PARTY_NOTICES.md).

## Lizenztexte im Paket

- macOS: in der App unter `Contents/Resources/licenses/`.
- Linux: im entpackten Ordner unter `_internal/licenses/`.

Dort stehen die übernommenen Lizenz-/Copyright-/Notice-Dateien und Qt-Attributionen. `BUILD-ENVIRONMENT.json` nennt die genauen Versionen, Projektquellen und die SHA-256-Prüfsummen der für Notices verwendeten Archive. Das Inventar umfasst auch Build-Werkzeuge und ist daher größer als die Menge der gebündelten Module.

## Qt / PySide / Shiboken 6.12.0

Die App lädt die Qt-Bibliotheken dynamisch und verwendet die LGPLv3-Option für die eingebundenen Qt-Module. Die LGPLv3- und zugehörigen GPLv3-Lizenztexte werden aus den Originalquellen im Paket mitgeliefert. Qt/PySide/Shiboken sind keine Bestandteile unter der MIT-Projektlizenz. Änderungen am gebündelten Qt werden nicht vorgenommen; PyInstaller passt lediglich Ladepfade und Verpackung an.

Passende Originalquellen:

- [Qt Base v6.12.0](https://github.com/qt/qtbase/tree/v6.12.0)
- [Qt SVG v6.12.0](https://github.com/qt/qtsvg/tree/v6.12.0)
- [Qt Image Formats v6.12.0](https://github.com/qt/qtimageformats/tree/v6.12.0)
- [PySide und Shiboken v6.12.0](https://github.com/pyside/pyside-setup/tree/v6.12.0)
- [Qt Build-Anleitung](https://doc.qt.io/qt-6/build-sources.html)
- [Qt for Python Build-Anleitung](https://doc.qt.io/qtforpython-6/building_from_source/index.html)

Für den Austausch zunächst eine Kopie des Pakets anlegen. Die ABI-kompatiblen Frameworks/Bibliotheken liegen auf macOS in `Contents/Frameworks/` und auf Linux in `_internal/`, insbesondere unter `PySide6/Qt/`. Durch selbst gebaute kompatible Versionen ersetzen, zusammen mit den passenden PySide-/Shiboken-Bindings. Anschließend den Pakettest und die Anwendung prüfen. Änderungen können macOS-Signaturen ungültig machen; die geänderte Kopie bei Bedarf selbst ad hoc signieren. Alternativ die vollständig offenen App-Quellen mit den eigenen Qt/PySide-Versionen gemäß [Build-Anleitung](building.md) neu paketieren.

Die Projektlizenz schränkt Änderungen oder Reverse Engineering zur Fehlersuche an solchen Bibliotheksänderungen nicht ein. Weitere Hinweise: [Qt Open Source Obligations](https://www.qt.io/development/open-source-lgpl-obligations), [Qt for Python Licenses](https://doc.qt.io/qtforpython-6/licenses.html).
