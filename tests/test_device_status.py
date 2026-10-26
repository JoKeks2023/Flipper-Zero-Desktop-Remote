import unittest

from core.device_status import DeviceStatus, measurement, parse_properties, read_device_status


class DeviceStatusTest(unittest.TestCase):
    def test_properties_keep_colons_in_values(self):
        self.assertEqual(parse_properties(' name : Test\nurl: https://example.org\ninvalid'),
                         {'name': 'Test', 'url': 'https://example.org'})

    def test_optional_power_failure_preserves_device_connection_result(self):
        calls = []
        def send(command, **kwargs):
            calls.append(command)
            if command == 'device_info':
                return 'hardware_name: Test'
            raise RuntimeError('Unknown command')
        status = read_device_status(send)
        self.assertEqual(status.device, {'hardware_name': 'Test'})
        self.assertEqual(set(status.errors), {'power', 'debug'})
        self.assertIsNone(status.charge_level)
        self.assertIsNotNone(status.received_at)
        self.assertEqual(calls, ['device_info', 'info power', 'info power_debug'])

    def test_missing_invalid_and_new_schema_are_not_zero(self):
        for value in ('nan', 'inf', '-1', '101', 'bad'):
            self.assertIsNone(DeviceStatus(power={'format.major': '2', 'charge.level': value}).charge_level)
        self.assertIsNone(DeviceStatus().number('battery.current'))
        self.assertIsNone(DeviceStatus(power={'format.major': '3', 'battery.voltage': '4000'}).number('battery.voltage'))
        self.assertEqual(measurement(None, 'V'), '—')
        self.assertEqual(measurement(0, 'mA'), '0 mA')

    def test_charge_state_is_independent_of_usb_voltage(self):
        status = DeviceStatus(power={'format.major': '2', 'charge.level': '0',
                                     'charge.state': 'discharging', 'battery.current': '-25'},
                              debug={'format.major': '1', 'charger.vbus': '5100'})
        self.assertEqual(status.charge_level, 0)
        self.assertEqual(status.charge_state, 'Lädt nicht')
        self.assertEqual(status.number('battery.current'), -25)
        self.assertEqual(status.number('charger.vbus', debug=True), 5100)

    def test_cancel_does_not_start_more_queries(self):
        calls = []
        def send(command, **kwargs):
            calls.append(command)
            return 'hardware_name: Test'
        with self.assertRaises(InterruptedError):
            read_device_status(send, cancelled=lambda: bool(calls))
        self.assertEqual(calls, ['device_info'])
