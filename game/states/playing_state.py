"""Playing state: normal active gameplay."""
import pygame as pg

from .base import GameState


class PlayingState(GameState):
    def __init__(self, gc, renderer) -> None:
        self._gc = gc
        self._renderer = renderer

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type != pg.KEYDOWN:
            return None
        if event.key in (pg.K_p, pg.K_PAUSE):
            return "paused"
        if event.key == pg.K_ESCAPE:
            self._gc.return_to_menu()
            return "menu"
        return None

    def update(self, dt: float) -> str | None:
        return self._gc.update_play(dt)

    def draw(self, screen: pg.Surface) -> None:
        self._gc.draw_play()
