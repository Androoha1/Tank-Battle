"""Minimal main menu: title + win target + start + quit."""
import math
import pygame as pg

from . import config


WIN_TARGETS = [5, 10, 0]
WIN_LABELS = ["First to 5", "First to 10", "Endless"]


class MenuItem:
    def __init__(self, label: str, kind: str, key: str | None = None) -> None:
        self.label = label
        self.kind = kind
        self.key = key


class Menu:
    def __init__(self, layout_controller) -> None:
        self._layout = layout_controller  # kept for symmetry; unused
        self._state = {"win_target": 0}
        self._items: list[MenuItem] = [
            MenuItem("WIN TARGET", "choice", "win_target"),
            MenuItem("START GAME", "action", "start"),
            MenuItem("QUIT", "action", "quit"),
        ]
        self._selected = 0
        self._pulse = 0.0
        self._title_font = pg.font.SysFont("arialblack", 130, bold=True)
        self._sub_font = pg.font.SysFont("arial", 22)
        self._row_font = pg.font.SysFont("arialblack", 30, bold=True)
        self._hint_font = pg.font.SysFont("arial", 16)

    # ---------------------------------------------------------------- input
    def handle_event(self, ev: pg.event.Event) -> dict | None:
        if ev.type != pg.KEYDOWN:
            return None
        item = self._items[self._selected]
        if ev.key in (pg.K_UP, pg.K_w):
            self._selected = (self._selected - 1) % len(self._items)
        elif ev.key in (pg.K_DOWN, pg.K_s):
            self._selected = (self._selected + 1) % len(self._items)
        elif ev.key in (pg.K_LEFT, pg.K_a):
            self._cycle(-1)
        elif ev.key in (pg.K_RIGHT, pg.K_d):
            self._cycle(1)
        elif ev.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
            if item.kind == "action":
                if item.key == "start":
                    return self.start_payload()
                if item.key == "quit":
                    return {"action": "quit"}
        elif ev.key == pg.K_ESCAPE:
            return {"action": "quit"}
        return None

    def _cycle(self, delta: int) -> None:
        item = self._items[self._selected]
        if item.kind != "choice" or item.key is None:
            return
        if item.key == "win_target":
            self._state["win_target"] = (self._state["win_target"] + delta) % len(WIN_TARGETS)

    def start_payload(self) -> dict:
        return {
            "action": "start",
            "win_target": WIN_TARGETS[self._state["win_target"]],
        }

    def update(self, dt: float) -> None:
        self._pulse = (self._pulse + dt * 0.005) % math.tau

    # ---------------------------------------------------------------- draw
    def draw(self, surface: pg.Surface, bg: pg.Surface) -> None:
        surface.blit(bg, (0, 0))

        # Title
        title = self._title_font.render("TANKONS", True, (240, 245, 255))
        title_rect = title.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 160))
        surface.blit(title, title_rect)

        sub = self._sub_font.render("local 2-player tank battle", True, (150, 165, 195))
        surface.blit(sub, sub.get_rect(center=(config.WIDTH // 2, title_rect.bottom + 8)))

        # Menu rows, centred vertically below the title.
        center_x = config.WIDTH // 2
        y = title_rect.bottom + 80
        for i, item in enumerate(self._items):
            self._draw_row(surface, item, center_x, y, i == self._selected)
            y += 70

        # Footer hint
        hint = self._hint_font.render(
            "W/S : select       A/D : change       ENTER : confirm       ESC : quit",
            True, (130, 145, 175),
        )
        surface.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT - 40)))

    def _draw_row(self, surface, item: MenuItem, cx: int, y: int, selected: bool) -> None:
        if item.kind == "choice":
            val = WIN_LABELS[self._state["win_target"]] if item.key == "win_target" else ""
            text = f"{item.label}    {val}"
        else:
            text = item.label

        color = (240, 245, 255) if selected else (160, 175, 200)
        surf = self._row_font.render(text, True, color)
        rect = surf.get_rect(center=(cx, y))
        surface.blit(surf, rect)

        if selected:
            pulse = (math.sin(self._pulse * 6) + 1) / 2
            arrow_color = (140 + int(60 * pulse), 200, 255)
            # left chevron
            pg.draw.polygon(surface, arrow_color, [
                (rect.left - 30, rect.centery - 10),
                (rect.left - 14, rect.centery),
                (rect.left - 30, rect.centery + 10),
            ])
            # right chevron
            pg.draw.polygon(surface, arrow_color, [
                (rect.right + 30, rect.centery - 10),
                (rect.right + 14, rect.centery),
                (rect.right + 30, rect.centery + 10),
            ])
