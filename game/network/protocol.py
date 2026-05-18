"""Length-prefixed JSON framing over TCP."""
import json
import socket
import struct


def _recv_all(sock: socket.socket, n: int) -> bytes | None:
    data = bytearray()
    while len(data) < n:
        try:
            chunk = sock.recv(n - len(data))
        except OSError:
            return None
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)


def send_msg(sock: socket.socket, msg: dict) -> None:
    data = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_msg(sock: socket.socket) -> dict | None:
    header = _recv_all(sock, 4)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    if length == 0 or length > 16 * 1024 * 1024:
        return None
    body = _recv_all(sock, length)
    if body is None:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
