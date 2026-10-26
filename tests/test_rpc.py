import unittest
from unittest.mock import patch
from core.rpc_display import RpcDisplay, varint, read_varint, fields, message, uint
from test_core import Port
from ui.screen import frame_image


class RPCPort(Port):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.requests = []
    def read_until(self, *args):
        return b'start_rpc_session\r\n'
    def write(self, payload):
        if payload == b'start_rpc_session\r':
            return len(payload)
        length, offset = read_varint(payload)
        packet = fields(payload[offset:])
        self.requests.append(packet)
        ack = uint(1, packet[1]) + message(4, b'')
        self.incoming.put(varint(len(ack)) + ack)
        if 20 in packet:
            frame = message(22, message(1, b'\xff' * 1024))
            self.incoming.put(varint(len(frame)) + frame)
        return len(payload)


class RPCTest(unittest.TestCase):
    def test_varint_bounds_and_unknown_fields(self):
        for value in [0, 127, 128, 1024, 65536]:
            self.assertEqual(read_varint(varint(value))[0], value)
        with self.assertRaises(EOFError):
            read_varint(b'\x80')
        with self.assertRaises(ValueError):
            read_varint(b'\x80' * 11)
        self.assertEqual(fields(uint(123, 42) + message(22, b'frame'))[22], b'frame')
    def test_input_sequence_and_stream_protocol(self):
        port = RPCPort()
        display = RpcDisplay()
        with patch('core.rpc_display.serial.Serial', return_value=port):
            try:
                display.connect('test')
                display.input('up', long=True)
                inputs = [fields(p[23]) for p in port.requests if 23 in p]
                self.assertEqual([p[2] for p in inputs], [0, 3, 1])
                self.assertEqual(display.frame_count, 1)
                self.assertEqual(len(display.pop_frame()[0]), 1024)
            finally:
                display.disconnect()
        self.assertFalse(display.is_connected)
    def test_bitmap_layout_and_rotation(self):
        frame = bytearray(1024)
        frame[0] = 1
        image = frame_image(bytes(frame))
        self.assertNotEqual(image.pixel(0, 0), image.pixel(1, 0))
        self.assertEqual(image.pixel(0, 1), image.pixel(1, 0))
        self.assertEqual(frame_image(bytes(frame), 2).width(), 64)
        with self.assertRaises(ValueError):
            frame_image(b'bad')
