"""Authoritative game server. Per the technical design, the server runs the
simulation and broadcasts state to all clients each frame.

This implementation is intentionally lightweight: TCP, JSON framing,
threaded accept + per-client recv. The GameController is responsible for
calling :meth:`broadcast` each tick and reading inputs via :meth:`get_input`.
"""
import socket
import threading

from . import protocol


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5555, max_clients: int = 3) -> None:
        self._host = host
        self._port = port
        self._max = max_clients
        self._sock: socket.socket | None = None
        self._clients: list[tuple[int, socket.socket]] = []
        self._lock = threading.Lock()
        self._inputs: dict[int, dict] = {}
        self._running = False
        self._accept_thread: threading.Thread | None = None
        self._error: str | None = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def connected_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def start(self) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self._host, self._port))
            s.listen(self._max)
            self._sock = s
        except OSError as e:
            self._error = str(e)
            return False
        self._running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        return True

    def _accept_loop(self) -> None:
        while self._running and self._sock:
            try:
                conn, _addr = self._sock.accept()
            except OSError:
                return
            with self._lock:
                if len(self._clients) >= self._max:
                    try:
                        conn.close()
                    except OSError:
                        pass
                    continue
                # Slot 0 is reserved for the host; clients get 1..N
                used = {s for s, _ in self._clients}
                slot = next(i for i in range(1, self._max + 2) if i not in used)
                self._clients.append((slot, conn))
            try:
                protocol.send_msg(conn, {"t": "WELCOME", "slot": slot})
            except OSError:
                self._disconnect(slot, conn)
                continue
            threading.Thread(target=self._recv_loop, args=(slot, conn), daemon=True).start()

    def _recv_loop(self, slot: int, conn: socket.socket) -> None:
        while self._running:
            msg = protocol.recv_msg(conn)
            if msg is None:
                self._disconnect(slot, conn)
                return
            if msg.get("t") == "INPUT":
                with self._lock:
                    self._inputs[slot] = msg

    def _disconnect(self, slot: int, conn: socket.socket) -> None:
        with self._lock:
            self._clients = [(s, c) for s, c in self._clients if c is not conn]
            self._inputs.pop(slot, None)
        try:
            conn.close()
        except OSError:
            pass

    def get_input(self, slot: int) -> dict:
        with self._lock:
            return dict(self._inputs.get(slot, {}))

    def connected_slots(self) -> list[int]:
        with self._lock:
            return sorted(s for s, _ in self._clients)

    def broadcast(self, msg: dict) -> None:
        with self._lock:
            conns = list(self._clients)
        dead = []
        for slot, conn in conns:
            try:
                protocol.send_msg(conn, msg)
            except OSError:
                dead.append((slot, conn))
        for slot, conn in dead:
            self._disconnect(slot, conn)

    def stop(self) -> None:
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        with self._lock:
            for _, conn in self._clients:
                try:
                    conn.close()
                except OSError:
                    pass
            self._clients = []
