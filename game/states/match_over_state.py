"""Match-over state: final scores screen after a player wins the match."""
import pygame as pg

from .base import GameState
from .. import config


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

        overlay = pg.Surface((config.WIDTH, config.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        match_winner = self._gc.match_winner
        players_ctrl = self._gc.players_ctrl
        if match_winner:
            text = f"{match_winner.name} WINS THE MATCH"
            color = match_winner.colors["accent"]
        else:
            text = "MATCH OVER"
            color = (220, 220, 230)
        surf = self._renderer.title_font.render(text, True, color)
        rect = surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30))
        screen.blit(surf, rect)

        y = rect.bottom + 30
        for p in players_ctrl.players:
            s = self._renderer.sub_font.render(
                f"{p.name}: {players_ctrl.scores.get(p, 0)}", True, p.colors["accent"]
            )
            screen.blit(s, s.get_rect(center=(config.WIDTH // 2, y)))
            y += 36

        hint = self._renderer.tiny_font.render(
            "Press ENTER or ESC to return to menu", True, (180, 190, 210)
        )
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 60)))
