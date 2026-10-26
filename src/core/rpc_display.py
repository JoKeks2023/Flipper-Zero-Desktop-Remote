"""Small, bounded implementation of Flipper's public protobuf screen/input subset.

Wire fields: flipperdevices/flipperzero-protobuf (gui.proto, flipper.proto).
Unknown fields (including Momentum screen colors) are skipped by wire type.
"""
from __future__ import annotations

import threading
import time

import serial


def varint(value: int) -> bytes:
    if value < 0:
        raise ValueError('Expected unsigned integer')
    result = bytearray()
    while value > 127:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def read_varint(data: bytes, offset=0):
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise EOFError('Incomplete varint')
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if not byte & 128:
            return value, offset
    raise ValueError('Oversized varint')


def uint(field, value):
    return varint(field << 3) + varint(value)


def message(field, payload):
    return varint((field << 3) | 2) + varint(len(payload)) + payload


def fields(data):
    result = {}
    offset = 0
    while offset < len(data):
        tag, offset = read_varint(data, offset)
        field, kind = tag >> 3, tag & 7
        if not field:
            raise ValueError('Invalid protobuf field')
        if kind == 0:
            value, offset = read_varint(data, offset)
        elif kind == 2:
            length, offset = read_varint(data, offset)
            value = data[offset:offset + length]
            if len(value) != length:
                raise EOFError('Incomplete field')
            offset += length
        elif kind in {1, 5}:
            length = 8 if kind == 1 else 4
            value = data[offset:offset + length]
            if len(value) != length:
                raise EOFError('Incomplete fixed field')
            offset += length
        else:
            raise ValueError(f'Unsupported protobuf wire type: {kind}')
        result[field] = value
    return result


class RpcDisplay:
    def __init__(self):
        self.connection = None
        self.thread = None
        self.stop = threading.Event()
        self.condition = threading.Condition()
        self.write_lock = threading.Lock()
        self.next_id = 0
        self.responses = {}
        self.frame = None
        self.frame_count = 0
        self.error = None

    @property
    def is_connected(self):
        return bool(self.connection and self.connection.is_open and not self.error)

    def connect(self, port):
        self.disconnect()
        self.error = None
        self.frame = None
        self.frame_count = 0
        self.connection = serial.Serial(port, 115200, timeout=.1, write_timeout=2)
        try:
            welcome = bytearray()
            deadline = time.monotonic() + 5
            while not welcome.endswith(b'>: ') and time.monotonic() < deadline:
                welcome.extend(self.connection.read(self.connection.in_waiting or 1))
                if len(welcome) > 16384:
                    raise RuntimeError('Unexpected CLI handshake')
            if not welcome.endswith(b'>: '):
                raise TimeoutError('Flipper did not open CLI')
            self.connection.write(b'start_rpc_session\r')
            echo = self.connection.read_until(b'\n', 256)
            if b'start_rpc_session' not in echo:
                raise RuntimeError(f'RPC handshake failed: {echo!r}')
            self.stop = threading.Event()
            self.responses = {}
            self.thread = threading.Thread(target=self._reader, daemon=True)
            self.thread.start()
            self.request(20)
        except Exception:
            self.disconnect()
            raise

    def request(self, field, payload=b'', timeout=3):
        with self.write_lock:
            with self.condition:
                if not self.is_connected:
                    raise RuntimeError(self.error or 'Display is disconnected')
                self.next_id += 1
                request_id = self.next_id
            packet = uint(1, request_id) + message(field, payload)
            self.connection.write(varint(len(packet)) + packet)
        deadline = time.monotonic() + timeout
        with self.condition:
            while request_id not in self.responses:
                if not self.is_connected:
                    raise RuntimeError(self.error or 'Display disconnected')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('No RPC acknowledgement from Flipper')
                self.condition.wait(remaining)
            status = self.responses.pop(request_id)
        if status:
            raise RuntimeError(f'Flipper rejected RPC command (status {status})')

    def input(self, key, long=False):
        keys = {'up': 0, 'down': 1, 'right': 2, 'left': 3, 'ok': 4, 'back': 5}
        code = keys[key]
        try:
            self.request(23, uint(1, code) + uint(2, 0))
            self.request(23, uint(1, code) + uint(2, 3 if long else 2))
        finally:
            if self.is_connected:
                self.request(23, uint(1, code) + uint(2, 1))

    def pop_frame(self):
        with self.condition:
            frame, self.frame = self.frame, None
            return frame

    def _reader(self):
        buffer = bytearray()
        connection = self.connection
        try:
            while not self.stop.is_set():
                chunk = connection.read(connection.in_waiting or 1)
                if not chunk:
                    continue
                buffer.extend(chunk)
                while buffer:
                    try:
                        length, offset = read_varint(buffer)
                    except EOFError:
                        break
                    if length > 65536:
                        raise ValueError('Oversized RPC packet')
                    if len(buffer) < offset + length:
                        break
                    packet = fields(bytes(buffer[offset:offset + length]))
                    del buffer[:offset + length]
                    with self.condition:
                        if 22 in packet:
                            frame = fields(packet[22])
                            if len(frame.get(1, b'')) == 1024:
                                self.frame = (frame[1], frame.get(2, 0))
                                self.frame_count += 1
                        elif packet.get(1):
                            self.responses[packet[1]] = packet.get(2, 0)
                        self.condition.notify_all()
        except Exception as exc:
            if not self.stop.is_set():
                with self.condition:
                    self.error = str(exc)
                    self.condition.notify_all()
        finally:
            connection.close()

    def disconnect(self, graceful=True):
        connection = self.connection
        if graceful and self.is_connected and self.thread and self.thread.is_alive():
            try:
                self.request(21, timeout=1)
                self.request(19, timeout=1)
            except Exception:
                pass
        self.stop.set()
        with self.condition:
            self.connection = None
            self.condition.notify_all()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=1)
        if connection:
            connection.close()
        self.thread = None
