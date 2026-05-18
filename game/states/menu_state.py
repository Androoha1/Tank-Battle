"""Menu state: shows the main menu."""
import pygame as pg

from .base import GameState


class MenuState(GameState):
    def __init__(self, gc, menu, renderer) -> None:
        self._gc = gc
        self._menu = menu
        self._renderer = renderer

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type != pg.KEYDOWN:
            return None
        action = self._menu.handle_event(event)
        if action:
            if action["action"] == "quit":
                return "quit"
            if action["action"] == "start":
                self._gc.begin_match(action["win_target"])
                return "playing"
        return None

    def update(self, dt: float) -> str | None:
        self._menu.update(dt)
        return None

    def draw(self, screen: pg.Surface) -> None:
        self._menu.draw(screen, self._renderer.background)
