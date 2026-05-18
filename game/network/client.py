"""Client. Sends local input to the server; mirrors broadcast state."""
import socket
import threading
from collections import deque

from . import protocol


class GameClient:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._running = False
        self._connected = False
        self._slot = -1
        self._lock = threading.Lock()
        self._state: dict | None = None
        self._events: deque[dict] = deque(maxlen=64)
        self._error: str | None = None

    @property
    def slot(self) -> int:
        return self._slot

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def error(self) -> str | None:
        return self._error

    def connect_async(self) -> None:
        threading.Thread(target=self.connect, daemon=True).start()

    def connect(self, timeout: float = 4.0) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((self._host, self._port))
            s.settimeout(None)
            welcome = protocol.recv_msg(s)
            if welcome is None or welcome.get("t") != "WELCOME":
                raise RuntimeError("no welcome from server")
            self._slot = int(welcome.get("slot", -1))
            self._sock = s
            self._running = True
            self._connected = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            return True
        except (OSError, RuntimeError) as e:
            self._error = str(e)
            return False

    def _recv_loop(self) -> None:
        assert self._sock is not None
        while self._running:
            msg = protocol.recv_msg(self._sock)
            if msg is None:
                self._connected = False
                return
            kind = msg.get("t")
            if kind == "STATE":
                with self._lock:
                    self._state = msg
            elif kind == "EVENT":
                with self._lock:
                    self._events.append(msg)

    def latest_state(self) -> dict | None:
        with self._lock:
            return self._state

    def drain_events(self) -> list[dict]:
        with self._lock:
            out = list(self._events)
            self._events.clear()
        return out

    def send_input(self, inputs: dict) -> None:
        if not self._connected or self._sock is None:
            return
        try:
            protocol.send_msg(self._sock, {"t": "INPUT", **inputs})
        except OSError:
            self._connected = False

    def disconnect(self) -> None:
        self._running = False
        self._connected = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
