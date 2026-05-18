"""Match-over state: final scores screen after a player wins the match."""
import pygame as pg

from .base import GameState


class MatchOverState(GameState):
    def __init__(self, gc, renderer) -> None:
        self._gc = gc
        self._renderer = renderer

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_RETURN, pg.K_SPACE, pg.K_ESCAPE):
                self._gc.return_to_menu()
                return "menu"
        return None

    def update(self, dt: float) -> str | None:
        return None

    def draw(self, screen: pg.Surface) -> None:
        self._gc.draw_play()
        self._renderer.draw_match_over(screen, self._gc.match_winner, self._gc.players_ctrl)
