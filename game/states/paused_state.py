"""Paused state: game world is frozen; shows pause overlay."""
import pygame as pg

from .base import GameState


class PausedState(GameState):
    def __init__(self, gc, renderer) -> None:
        self._gc = gc
        self._renderer = renderer
        self._pulse = 0.0

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type != pg.KEYDOWN:
            return None
        if event.key in (pg.K_p, pg.K_PAUSE, pg.K_ESCAPE, pg.K_RETURN):
            return "playing"
        if event.key == pg.K_q:
            self._gc.return_to_menu()
            return "menu"
        return None

    def update(self, dt: float) -> str | None:
        self._pulse += dt * 0.004
        return None

    def draw(self, screen: pg.Surface) -> None:
        self._gc.draw_play()
        self._renderer.draw_pause(screen, self._pulse)
