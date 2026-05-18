"""Round-end state: brief pause after a round; then starts next round or match-over."""
import pygame as pg

from .base import GameState
from .. import config


class RoundEndState(GameState):
    def __init__(self, gc, renderer) -> None:
        self._gc = gc
        self._renderer = renderer
        self._timer = 0.0

    def on_enter(self) -> None:
        self._timer = config.ROUND_END_DELAY_MS

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self._gc.return_to_menu()
            return "menu"
        return None

    def update(self, dt: float) -> str | None:
        self._gc.update_play(dt, ignore_winner_check=True)
        self._timer -= dt
        if self._timer <= 0:
            if self._gc.match_winner is not None:
                return "match_over"
            self._gc.start_round()
            return "playing"
        return None

    def draw(self, screen: pg.Surface) -> None:
        self._gc.draw_play()
        self._renderer.draw_round_end(screen, self._gc.winner)
