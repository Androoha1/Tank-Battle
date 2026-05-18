"""Menu state: shows the main menu."""
import math
import pygame as pg

from .base import GameState
from .. import config

WIN_TARGETS = [5, 10, 0]
WIN_LABELS = ["First to 5", "First to 10", "Endless"]

_ROWS = (
    ("WIN TARGET", "choice"),
    ("START GAME", "start"),
    ("QUIT", "quit"),
)


class MenuState(GameState):
    def __init__(self, gc, renderer) -> None:
        self._gc = gc
        self._renderer = renderer
        self._selected = 0
        self._win_target_idx = 0
        self._pulse = 0.0
        self._title_font = pg.font.SysFont("arialblack", 130, bold=True)
        self._sub_font = pg.font.SysFont("arial", 22)
        self._row_font = pg.font.SysFont("arialblack", 30, bold=True)
        self._hint_font = pg.font.SysFont("arial", 16)

    def handle_event(self, event: pg.event.Event) -> str | None:
        if event.type != pg.KEYDOWN:
            return None
        if event.key in (pg.K_UP, pg.K_w):
            self._selected = (self._selected - 1) % len(_ROWS)
        elif event.key in (pg.K_DOWN, pg.K_s):
            self._selected = (self._selected + 1) % len(_ROWS)
        elif event.key in (pg.K_LEFT, pg.K_a):
            if _ROWS[self._selected][1] == "choice":
                self._win_target_idx = (self._win_target_idx - 1) % len(WIN_TARGETS)
        elif event.key in (pg.K_RIGHT, pg.K_d):
            if _ROWS[self._selected][1] == "choice":
                self._win_target_idx = (self._win_target_idx + 1) % len(WIN_TARGETS)
        elif event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
            kind = _ROWS[self._selected][1]
            if kind == "start":
                self._gc.begin_match(WIN_TARGETS[self._win_target_idx])
                return "playing"
            if kind == "quit":
                return "quit"
        elif event.key == pg.K_ESCAPE:
            return "quit"
        return None

    def update(self, dt: float) -> str | None:
        self._pulse = (self._pulse + dt * 0.005) % math.tau
        return None

    def draw(self, screen: pg.Surface) -> None:
        screen.blit(self._renderer.background, (0, 0))

        title = self._title_font.render("TANKONS", True, (240, 245, 255))
        title_rect = title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 160))
        screen.blit(title, title_rect)

        sub = self._sub_font.render("local 2-player tank battle", True, (150, 165, 195))
        screen.blit(sub, sub.get_rect(center=(config.WIDTH // 2, title_rect.bottom + 8)))

        center_x = config.WIDTH // 2
        y = title_rect.bottom + 80
        for i, row in enumerate(_ROWS):
            self._draw_row(screen, row, center_x, y, i == self._selected)
            y += 70

        hint = self._hint_font.render(
            "W/S : select       A/D : change       ENTER : confirm       ESC : quit",
            True, (130, 145, 175),
        )
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 40)))

    def _draw_row(self, surface: pg.Surface, row: tuple, cx: int, y: int, selected: bool) -> None:
        label, kind = row
        if kind == "choice":
            text = f"{label}    {WIN_LABELS[self._win_target_idx]}"
        else:
            text = label

        color = (240, 245, 255) if selected else (160, 175, 200)
        surf = self._row_font.render(text, True, color)
        rect = surf.get_rect(center=(cx, y))
        surface.blit(surf, rect)

        if selected:
            pulse = (math.sin(self._pulse * 6) + 1) / 2
            arrow_color = (140 + int(60 * pulse), 200, 255)
            pg.draw.polygon(surface, arrow_color, [
                (rect.left - 30, rect.centery - 10),
                (rect.left - 14, rect.centery),
                (rect.left - 30, rect.centery + 10),
            ])
            pg.draw.polygon(surface, arrow_color, [
                (rect.right + 30, rect.centery - 10),
                (rect.right + 14, rect.centery),
                (rect.right + 30, rect.centery + 10),
            ])
