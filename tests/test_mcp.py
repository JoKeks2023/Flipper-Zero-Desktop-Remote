import asyncio
import base64
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from PySide6.QtTest import QTest

from flipper_mcp.bridge_client import BridgeClient, MAX_REQUEST
from flipper_mcp.ipc import LocalBridge
from persistence.config_store import ConfigStore
from ui.app import MainWindow
from test_ui import APP, FakeClient


class MCPTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'bridge.sock'
        with patch('persistence.config_store.ensure_app_dirs', return_value=Path(self.temp.name)):
            self.store = ConfigStore('Test')
        with patch('flipper_mcp.ipc.default_socket_path', return_value=self.path):
            self.window = MainWindow(self.store, FakeClient(), lambda: ['/dev/test'])
        self.window.show()
        self.window.connect_device()
        self.wait_for(lambda: not self.window.busy)
        self.bridge = BridgeClient(self.path, timeout=3)

    def tearDown(self):
        self.wait_for(lambda: not self.window.busy)
        self.window.close()
        APP.processEvents()
        self.temp.cleanup()

    def wait_for(self, predicate):
        for _ in range(2000):
            APP.processEvents()
            if predicate():
                return
            QTest.qWait(10)
        self.fail('Qt operation did not complete')

    def run_thread(self, work):
        results, errors = [], []
        def run():
            try:
                results.append(work())
            except BaseException as exc:
                errors.append(exc)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.wait_for(lambda: not thread.is_alive())
        if errors:
            raise errors[0]
        return results[0]

    def call(self, operation, **arguments):
        return self.run_thread(lambda: self.bridge.call(operation, **arguments))

    def enable(self, control=False):
        self.window.mcp_panel.enabled.setChecked(True)
        self.window.mcp_panel.permission.setCurrentIndex(1 if control else 0)

    def test_disabled_enabled_and_revoked_local_access(self):
        with self.assertRaisesRegex(RuntimeError, 'aktivieren'):
            self.bridge.call('status')
        self.enable()
        result = self.call('status')
        self.assertTrue(result['connected'])
        self.assertEqual(result['permission'], 'read_only')
        self.assertEqual(result['power']['charge.level'], '98')
        self.assertEqual(self.path.parent.stat().st_mode & 0o077, 0)
        self.assertIn('status', self.window.mcp_panel.last_action.text())
        self.window.mcp_panel.enabled.setChecked(False)
        with self.assertRaisesRegex(RuntimeError, 'aktivieren'):
            self.bridge.call('status')

    def test_storage_uses_existing_connection_and_errors_are_not_success(self):
        self.enable()
        listing = self.call('list_directory', path='/ext/infrared')
        self.assertEqual(listing['entries'][1]['path'], '/ext/infrared/Canon RC-6.ir')
        result = self.call('read_text', path='/ext/infrared/Canon RC-6.ir')
        self.assertTrue(result['text'].startswith('Filetype:'))
        self.assertNotIn('Size: 131', result['text'])
        self.assertTrue(result['untrusted_content'])
        self.assertEqual(result['size'], 131)
        with self.assertRaisesRegex(RuntimeError, 'Gerätepfad'):
            self.call('read_text', path='/ext/../private.txt')
        with self.assertRaises(RuntimeError):
            self.call('list_directory', path='/ext/a"\rpower reboot')
        with self.assertRaisesRegex(RuntimeError, 'Textdateien'):
            self.call('read_text', path='/ext/app.fap')

    def test_control_requires_separate_permission_and_sends_one_event(self):
        self.enable()
        self.window.client.commands.clear()
        with self.assertRaisesRegex(RuntimeError, 'nicht freigegeben'):
            self.call('press_key', key='up', long=True)
        self.assertEqual(self.window.client.commands, [])
        self.window.mcp_panel.permission.setCurrentIndex(1)
        self.assertTrue(self.call('press_key', key='up', long=True)['sent'])
        self.assertEqual(self.window.client.commands, ['input send up long'])
        self.window.mcp_panel.permission.setCurrentIndex(0)
        with self.assertRaisesRegex(RuntimeError, 'nicht freigegeben'):
            self.call('press_key', key='back')

    def test_cached_status_remains_available_while_device_busy(self):
        self.enable()
        gate = threading.Event()
        self.window.submit('busy', lambda: gate.wait(3))
        try:
            self.assertTrue(self.call('status')['busy'])
            with self.assertRaisesRegex(RuntimeError, 'beschäftigt'):
                self.call('list_directory', path='/ext')
        finally:
            gate.set()

    def test_live_frame_is_png_and_storage_never_interrupts_live_mode(self):
        self.enable()
        self.window.screen.set_frame(bytes(1024))
        self.window.frame_time = datetime.now().astimezone()
        with patch.object(type(self.window.rpc), 'is_connected', new_callable=lambda: property(lambda _: True)):
            result = self.call('get_screen')
            self.assertTrue(base64.b64decode(result['image']).startswith(b'\x89PNG'))
            with self.assertRaisesRegex(RuntimeError, 'Live-Ansicht'):
                self.call('list_directory', path='/ext')
            with self.assertRaisesRegex(RuntimeError, 'Live-Ansicht'):
                self.call('status', refresh=True)

    def test_duplicate_server_cannot_steal_socket(self):
        self.enable()
        second = LocalBridge(lambda *args: None, path=self.path)
        try:
            with self.assertRaisesRegex(RuntimeError, 'bereits'):
                second.start()
            self.assertTrue(self.call('status')['connected'])
        finally:
            second.stop()

    def test_invalid_and_oversized_ipc_requests_are_bounded(self):
        self.enable()
        def request(payload):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(3)
                client.connect(str(self.path))
                client.sendall(payload)
                return json.loads(client.recv(65536))
        self.assertIn('error', self.run_thread(lambda: request(b'[]\n')))
        self.assertIn('error', self.run_thread(lambda: request(b'x' * (MAX_REQUEST + 1))))
        with self.assertRaisesRegex(RuntimeError, 'Argumente'):
            self.call('status', arbitrary='ignored')

    @unittest.skipUnless(importlib.util.find_spec('mcp'), 'optional MCP SDK not installed')
    def test_real_mcp_stdio_client_discovers_tools_and_calls_desktop_bridge(self):
        from mcp.client import Client
        from mcp.client.stdio import StdioServerParameters
        self.enable()
        async def exercise():
            parameters = StdioServerParameters(command=sys.executable,
                args=['-m', 'flipper_mcp.server', '--socket', str(self.path)])
            async with Client(parameters, mode='legacy') as client:
                tools = (await client.list_tools()).tools
                self.assertEqual(len(tools), 6)
                status = await client.call_tool('flipper_status')
                self.assertFalse(status.is_error)
                self.assertEqual(status.structured_content['power']['charge.level'], '98')
                denied = await client.call_tool('flipper_press_key', {'key': 'up'})
                self.assertTrue(denied.is_error)
                invalid = await client.call_tool('flipper_press_key', {'key': 'arbitrary'})
                self.assertTrue(invalid.is_error)
                listing = await client.call_tool('flipper_list_directory', {'path': '/ext/infrared'})
                self.assertFalse(listing.is_error)
                self.assertEqual(len(listing.structured_content['entries']), 2)
                return True
        self.assertTrue(self.run_thread(lambda: asyncio.run(exercise())))
