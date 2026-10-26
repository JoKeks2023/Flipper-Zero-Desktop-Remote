import queue
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from core.flipper_api import FlipperAPI
from core.serial_client import SerialClient
from core.storage import parse_listing, quote_path
from persistence.config_store import ConfigStore


class Port:
    def __init__(self, **kwargs):
        self.port = kwargs.get('port', 'test')
        self.is_open = True
        self.incoming = queue.Queue()
        self.incoming.put(b'Welcome\r\n>: ')
        self.writes = []
        self.responses = {}
        self.in_waiting = 0
    def read(self, size):
        try:
            value = self.incoming.get(timeout=.01)
        except queue.Empty:
            return b''
        if isinstance(value, Exception):
            raise value
        return value
    def write(self, payload):
        self.writes.append(payload)
        if payload == b'\x03':
            self.incoming.put(b'Interrupted\r\n>: ')
            return len(payload)
        command = payload.decode().strip()
        for chunk in self.responses.get(command, [payload + b'\nOK\r\n>: ']):
            self.incoming.put(chunk)
        return len(payload)
    def close(self):
        self.is_open = False


class SerialTest(unittest.TestCase):
    def setUp(self):
        self.port = Port()
        self.patch = patch('core.serial_client.serial.Serial', return_value=self.port)
        self.patch.start()
        self.client = SerialClient()
        self.client.connect('test')
    def tearDown(self):
        self.client.disconnect()
        self.patch.stop()
    def test_split_prompt_and_utf8(self):
        self.port.responses['test'] = [b'test\r\nGr\xc3', b'\xbc\xc3\x9fe\r\n>', b': ']
        self.assertEqual(self.client.send_command('test'), 'Grüße')
    def test_firmware_error_is_not_success(self):
        self.port.responses['bad'] = [b'bad\r\nStorage error: not found\r\n>: ']
        with self.assertRaisesRegex(RuntimeError, 'Storage error'):
            self.client.send_command('bad')
        self.assertTrue(self.client.is_connected)
    def test_timeout_interrupts_then_next_command_is_clean(self):
        self.port.responses['stream'] = [b'stream\r\nRunning\r\n']
        with self.assertRaises(TimeoutError):
            self.client.send_command('stream', timeout=.03)
        self.assertIn(b'\x03', self.port.writes)
        self.assertEqual(self.client.send_command('next'), 'OK')
    def test_read_error_marks_disconnected(self):
        self.port.responses['broken'] = [OSError('unplugged')]
        with self.assertRaisesRegex(RuntimeError, 'unplugged'):
            self.client.send_command('broken')
        self.assertFalse(self.client.is_connected)
    def test_rejects_multiline_and_control_commands(self):
        for command in ['', 'help\npower reboot', 'help\rpower reboot', 'help\x03']:
            with self.assertRaises(ValueError):
                self.client.send_command(command)
    def test_serializes_concurrent_callers(self):
        results = []
        threads = [threading.Thread(target=lambda n=n: results.append(self.client.send_command(f'cmd{n}'))) for n in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)
        self.assertEqual(results, ['OK'] * 5)


class StorageTest(unittest.TestCase):
    def test_listing_preserves_names_and_separates_sizes(self):
        entries = parse_listing('/ext/infrared', '\t[D] remote\n\t[F] Canon RC-6.ir 131b\n\tEmpty\nStorage error: no file\n>: ')
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].is_dir)
        self.assertEqual(entries[1].path, '/ext/infrared/Canon RC-6.ir')
        self.assertEqual(entries[1].size, 131)
    def test_path_validation(self):
        self.assertEqual(quote_path('/ext/a b.ir'), '"/ext/a b.ir"')
        for path in ['relative', '/ext/a\nhelp', '/ext/a"', '/ext/\x03']:
            with self.assertRaises(ValueError):
                quote_path(path)
    def test_single_long_event(self):
        sent = []
        FlipperAPI(sent.append).input_long('up')
        self.assertEqual(sent, ['input send up long'])


class PersistenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        with patch('persistence.config_store.ensure_app_dirs', return_value=Path(self.temp.name)):
            self.store = ConfigStore('Test')
    def tearDown(self):
        self.temp.cleanup()
    def test_empty_saved_macros_stay_empty(self):
        self.store.save_macros({})
        self.assertEqual(self.store.load_macros(), {})
    def test_partial_settings_merge_defaults(self):
        self.store.settings_file.write_text('{"theme":"light"}')
        settings = self.store.load_settings()
        self.assertEqual(settings['theme'], 'light')
        self.assertIs(settings['expert_mode'], False)
