import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QThread
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from core.storage import StorageEntry
from persistence.config_store import ConfigStore
from ui.app import MainWindow, MODULES, macro_allowed

APP = QApplication.instance() or QApplication([])


class FakeClient:
    is_connected = False
    def __init__(self):
        self.commands = []
        self.interrupted = False
    def connect(self, port):
        self.is_connected = True
    def disconnect(self):
        self.is_connected = False
    def pop_logs(self):
        return []
    def interrupt(self):
        self.interrupted = True
    def send_command(self, command, **kwargs):
        self.commands.append(command)
        if command == 'device_info':
            return 'hardware_model : Flipper Zero\nfirmware_origin_fork : Momentum'
        if command == 'info power':
            return ('format.major: 2\ncharge.level: 98\ncharge.state: discharging\n'
                    'battery.voltage: 3919\nbattery.current: 0\nbattery.temp: 20\n'
                    'battery.health: 100\ncapacity.remain: 2056\ncapacity.full: 2100')
        if command == 'info power_debug':
            return 'format.major: 1\ncharger.vbus: 5100\ncharger.vsys: 3984'
        if command.startswith('storage list'):
            return '\t[D] nested\n\t[F] Canon RC-6.ir 131b'
        if command.startswith('storage read'):
            return 'Filetype: IR signals file\nVersion: 1'
        return ''


class UITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        with patch('persistence.config_store.ensure_app_dirs', return_value=Path(self.temp.name)):
            self.store = ConfigStore('Test')
        self.client = FakeClient()
        self.window = MainWindow(self.store, self.client, lambda: ['/dev/test'])
        self.window.show()
    def tearDown(self):
        self.wait_idle()
        self.window.close()
        APP.processEvents()
        self.temp.cleanup()
    def wait_idle(self):
        for _ in range(300):
            APP.processEvents()
            if not self.window.busy:
                return
            QTest.qWait(10)
        self.fail('worker did not finish')
    def connect(self):
        self.window.connect_button.click()
        self.wait_idle()
    def test_connect_browse_read_and_disconnect(self):
        self.connect()
        self.assertEqual(self.window.info.topLevelItemCount(), 2)
        self.assertEqual(self.window.connection_label.text(), 'Verbunden')
        self.window.nav.setCurrentRow(MODULES.index("Infrared"))
        self.wait_idle()
        browser = self.window.browsers[1]
        self.assertEqual(browser.table.topLevelItemCount(), 2)
        browser.table.setCurrentItem(browser.table.topLevelItem(1))
        browser.read.click()
        self.wait_idle()
        self.assertIn('Filetype:', browser.preview.toPlainText())
        self.assertIn('storage read "/ext/infrared/Canon RC-6.ir"', self.client.commands)
        browser.activate(browser.table.topLevelItem(0), 0)
        self.wait_idle()
        self.assertEqual(browser.current_path, '/ext/infrared/nested')
        self.window.disconnect_button.click()
        self.assertEqual(browser.table.topLevelItemCount(), 0)
        self.assertEqual(self.window.info.topLevelItemCount(), 0)
        self.assertFalse(browser.isEnabled())
    def test_remote_sends_one_long_event(self):
        self.connect()
        self.window.nav.setCurrentRow(MODULES.index("Remote"))
        self.window.long_press.setChecked(True)
        button = next(b for b in self.window.device_controls if b.accessibleName() == 'Nach oben')
        button.click()
        self.wait_idle()
        self.assertEqual(self.client.commands[-1:], ['input send up long'])

    def test_dashboard_reads_formats_refreshes_and_clears_device_values(self):
        self.connect()
        dashboard = self.window.dashboard
        self.assertEqual(dashboard.metrics['battery'].text(), '98 %')
        self.assertEqual(dashboard.notes['battery'].text(), 'Lädt nicht')
        self.assertEqual(dashboard.metrics['usb'].text(), '5,10 V')
        self.assertEqual(dashboard.metrics['temperature'].text(), '20 °C')
        self.assertEqual(dashboard.values['voltage'].text(), '3,919 V')
        self.assertEqual(dashboard.values['current'].text(), '0 mA')
        self.assertEqual(dashboard.values['remaining'].text(), '2056 mAh')
        self.assertIn('Aktualisiert', dashboard.freshness.text())
        self.client.commands.clear()
        dashboard.refresh.click()
        self.wait_idle()
        self.assertEqual(self.client.commands, ['device_info', 'info power', 'info power_debug'])
        self.window.disconnect_device()
        self.assertEqual(dashboard.metrics['battery'].text(), '—')
        self.assertEqual(dashboard.values['remaining'].text(), '—')
        self.assertFalse(dashboard.refresh.isEnabled())

    def test_failed_power_refresh_never_keeps_previous_values_as_current(self):
        self.connect()
        original = self.client.send_command
        def send(command, **kwargs):
            if command == 'info power':
                raise RuntimeError('Unsupported power command')
            return original(command, **kwargs)
        self.client.send_command = send
        self.window.refresh_dashboard()
        self.wait_idle()
        dashboard = self.window.dashboard
        self.assertTrue(self.window.connected)
        self.assertEqual(dashboard.metrics['battery'].text(), '—')
        self.assertEqual(dashboard.values['current'].text(), '—')
        self.assertIn('Akku nicht verfügbar', dashboard.freshness.text())
        self.assertEqual(dashboard.metrics['usb'].text(), '5,10 V')

    def test_dashboard_fits_minimum_window_without_horizontal_scrolling(self):
        self.connect()
        for width, height in ((1080, 680), (960, 600)):
            self.window.resize(width, height)
            APP.processEvents()
            scroll = self.window.stack.widget(0)
            self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)

    def test_dashboard_poll_only_when_visible_idle_and_cli_owns_connection(self):
        self.connect()
        self.client.commands.clear()
        self.window.nav.setCurrentRow(MODULES.index('Remote'))
        self.window._poll_dashboard()
        self.assertEqual(self.client.commands, [])
        self.window.nav.setCurrentRow(0)
        self.wait_idle()
        self.assertIn('info power', self.client.commands)
        self.client.commands.clear()
        with patch.object(type(self.window.rpc), 'is_connected', new_callable=lambda: property(lambda _: True)):
            self.window._update_state()
            self.window._poll_dashboard()
            self.assertFalse(self.window.refresh_dashboard())
            self.assertFalse(self.window.dashboard.refresh.isEnabled())
            self.assertIn('pausiert', self.window.dashboard.freshness.text())
            self.assertEqual(self.client.commands, [])
        gate = threading.Event()
        self.window.submit('busy', lambda: gate.wait(2))
        self.window._poll_dashboard()
        self.assertEqual(self.client.commands, [])
        gate.set()
        self.wait_idle()
    def test_worker_leaves_ui_responsive_and_returns_on_main_thread(self):
        gate = threading.Event()
        result_threads = []
        self.window.submit('test', lambda: gate.wait(2), lambda _: result_threads.append(QThread.currentThread()), False)
        self.window.nav.setCurrentRow(MODULES.index("Einstellungen"))
        APP.processEvents()
        self.assertEqual(self.window.stack.currentIndex(), MODULES.index("Einstellungen"))
        gate.set()
        self.wait_idle()
        self.assertEqual(result_threads, [APP.thread()])
    def test_device_error_is_visible(self):
        self.connect()
        def fail():
            raise RuntimeError('Storage error: not found')
        self.window.submit('failure', fail)
        self.wait_idle()
        self.assertIn('Storage error: not found', self.window.log.toPlainText())
    def test_deleted_last_macro_stays_deleted(self):
        self.store.save_macros({'only': ['device_info']})
        self.window.macros = self.store.load_macros()
        self.window._refresh_macros()
        with patch.object(self.window, '_confirm', return_value=True):
            self.window.delete_macro()
        self.assertEqual(self.store.load_macros(), {})
    def test_safe_macros_do_not_allow_arbitrary_cli(self):
        self.assertTrue(macro_allowed('storage list /ext', False))
        self.assertFalse(macro_allowed('storage remove /ext/data', False))
        self.assertFalse(macro_allowed('subghz tx_from_file /ext/a.sub', False))
        self.assertFalse(macro_allowed('power reboot', False))

    def test_easy_mode_hides_cli_without_enabling_expert(self):
        self.assertEqual(self.window.mode.currentText(), 'Easy Mode')
        self.assertTrue(self.window.nav.item(MODULES.index('Makros')).isHidden())
        self.assertTrue(self.window.log_dock.isHidden())
        self.assertFalse(self.window.expert.isChecked())
        self.window.mode.setCurrentIndex(1)
        self.assertFalse(self.window.nav.item(MODULES.index('Makros')).isHidden())
        self.assertFalse(self.window.expert.isChecked())

    def test_accessibility_toggle_navigates_to_destination(self):
        self.window.nav.item(MODULES.index('Remote')).setChecked(True)
        self.assertEqual(self.window.stack.currentIndex(), MODULES.index('Remote'))

    def test_keyboard_remote_sends_input_only_in_remote_view(self):
        from PySide6.QtCore import Qt
        self.connect()
        page = self.window.stack.widget(MODULES.index('Remote'))
        self.window.nav.setCurrentRow(MODULES.index('Remote'))
        self.window.activateWindow()
        self.window.long_press.setFocus()
        QTest.qWait(30)
        QTest.keyClick(self.window.long_press, Qt.Key.Key_Right)
        self.wait_idle()
        self.assertEqual(self.client.commands[-1], 'input send right short')
