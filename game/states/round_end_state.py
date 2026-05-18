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

        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        screen.blit(overlay, (0, 0))

        winner = self._gc.winner
        if winner:
            text = f"{winner.name} WINS THE ROUND"
            color = winner.colors["accent"]
        else:
            text = "DRAW"
            color = (220, 220, 230)
        surf = self._renderer.sub_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))
        panel = pg.Surface((rect.width + 60, rect.height + 30), pg.SRCALPHA)
        pg.draw.rect(panel, (15, 18, 28, 220), panel.get_rect(), border_radius=10)
        pg.draw.rect(panel, (*color, 180), panel.get_rect(), border_radius=10, width=2)
        screen.blit(panel, panel.get_rect(center=rect.center).topleft)
        screen.blit(surf, rect)
