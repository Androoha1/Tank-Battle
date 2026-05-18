"""Observer pattern event bus for game-wide events.

The GameEventObservable lets entities publish notifications without coupling
to concrete listeners. The same bus is reused by the (currently disabled)
networking layer described in the technical design document.
"""
from collections import defaultdict
from enum import Enum, auto
from typing import Any, Callable


class GameEvent(Enum):
    SHOT_FIRED = auto()
    TANK_DESTROYED = auto()
    POWERUP_PICKED = auto()
    ROUND_RESET = auto()


Listener = Callable[[Any], None]


class GameEventObservable:
    """Tiny pub/sub bus."""

    def __init__(self) -> None:
        self._listeners: dict[GameEvent, list[Listener]] = defaultdict(list)

    def subscribe(self, event: GameEvent, listener: Listener) -> None:
        self._listeners[event].append(listener)

    def publish(self, event: GameEvent, payload: Any = None) -> None:
        for listener in self._listeners.get(event, ()):
            listener(payload)
