"""Paused state: game world is frozen; shows pause overlay."""
import math
import pygame as pg

from .base import GameState
from .. import config


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

        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        anim = (math.sin(self._pulse * 4) + 1) / 2
        title = self._renderer.title_font.render("PAUSED", True, (235, 240, 250))
        screen.blit(title, title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 60)))

        col = (int(140 + 80 * anim), 210, 255)
        hint = self._renderer.sub_font.render(
            "P / ESC : resume    ·    Q : quit to menu", True, col
        )
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 40)))
