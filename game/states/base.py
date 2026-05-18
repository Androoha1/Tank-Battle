"""Abstract base class for all game states."""
from abc import ABC, abstractmethod
import pygame as pg


class GameState(ABC):
    """One game-screen stage.

    :meth:`handle_event` and :meth:`update` return a transition key string
    (e.g. ``"playing"``, ``"paused"``, ``"quit"``) or ``None`` to stay in
    the current state.  :meth:`on_enter` is called once each time the state
    becomes active and is a no-op by default.
    """

    def on_enter(self) -> None:
        """Called once when this state becomes the active state."""

    @abstractmethod
    def handle_event(self, event: pg.event.Event) -> str | None:
        """Handle one pygame event; return a transition key or None."""

    @abstractmethod
    def update(self, dt: float) -> str | None:
        """Advance one frame; return a transition key or None."""

    @abstractmethod
    def draw(self, screen: pg.Surface) -> None:
        """Render the current frame onto *screen*."""
