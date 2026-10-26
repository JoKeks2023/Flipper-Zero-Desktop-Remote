"""Release check of the assembled desktop, without hardware or persistent settings."""
import json
from pathlib import Path
import tempfile

from PySide6.QtWidgets import QApplication
from persistence.config_store import ConfigStore
from ui.app import MainWindow


def run():
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    with tempfile.TemporaryDirectory() as directory:
        # The normal store API is used, with an isolated location supplied below.
        store = ConfigStore('Flipper Remote release check', base_dir=Path(directory))
        window = MainWindow(store=store, scan_ports=lambda: [])
        window.show()
        for theme in (1, 2):
            window.theme.setCurrentIndex(theme)
            for page in range(window.stack.count()):
                window.nav.setCurrentRow(page)
                app.processEvents()
            window.nav.setCurrentRow(0)
            window.resize(960, 600)
            app.processEvents()
            assert window.stack.widget(0).horizontalScrollBar().maximum() == 0
        from importlib.resources import files
        for name in ('LICENSE.txt', 'THIRD_PARTY_NOTICES.txt'):
            assert files('ui').joinpath('legal', name).read_text(encoding='utf-8').strip()
        assert not window.windowIcon().isNull()
        window.close()
        app.processEvents()
        print(json.dumps({'gui': 'OK', 'pages': 10, 'themes': 2, 'minimum_width': 960, 'legal_resources': 'OK'}))
