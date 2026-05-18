"""Spawns players, tracks scores, draws the HUD scoreboard."""
import pygame as pg

from ..entities.player import Player
from .. import config


class PlayerController:
    DEFAULT_CONTROLS: list[dict[str, int]] = [
        {"left": pg.K_a, "right": pg.K_d, "up": pg.K_w, "down": pg.K_s, "shoot": pg.K_LSHIFT},
        {"left": pg.K_LEFT, "right": pg.K_RIGHT, "up": pg.K_UP, "down": pg.K_DOWN, "shoot": pg.K_RETURN},
        {"left": pg.K_j, "right": pg.K_l, "up": pg.K_i, "down": pg.K_k, "shoot": pg.K_u},
        {"left": pg.K_KP4, "right": pg.K_KP6, "up": pg.K_KP8, "down": pg.K_KP5, "shoot": pg.K_KP0},
    ]

    def __init__(self, num_players: int, events) -> None:
        self._num = num_players
        self._events = events
        self._players: list[Player] = []
        self._font: pg.font.Font | None = None
        self._small: pg.font.Font | None = None

    # ----------------------------------------------------------------- core
    def spawn(self, spawn_points: list[tuple[float, float, float]]) -> None:
        self._players = []
        for i in range(self._num):
            sx, sy, angle = spawn_points[i]
            colors = config.PLAYER_COLORS[i]
            controls = self.DEFAULT_CONTROLS[i]
            name = colors["name"]
            p = Player(sx, sy, angle, colors, controls, name, self._events)
            self._players.append(p)

    def reset_for_new_round(self, spawn_points: list[tuple[float, float, float]]) -> None:
        for i, p in enumerate(self._players):
            sx, sy, angle = spawn_points[i]
            p.respawn(sx, sy, angle)

    @property
    def players(self) -> list[Player]:
        return self._players

    @property
    def num_players(self) -> int:
        return self._num

    def alive_players(self) -> list[Player]:
        return [p for p in self._players if p.alive()]

    # ----------------------------------------------------------------- HUD
    def _ensure_fonts(self) -> None:
        if self._font is None:
            self._font = pg.font.SysFont("arialblack", 22, bold=True)
        if self._small is None:
            self._small = pg.font.SysFont("arial", 14, bold=True)

    def draw_hud(self, surface: pg.Surface, match) -> None:
        self._ensure_fonts()
        pg.draw.rect(surface, config.HUD_BG, (0, 0, config.WIDTH, config.HUD_HEIGHT))
        pg.draw.line(surface, config.HUD_LINE, (0, config.HUD_HEIGHT - 1),
                     (config.WIDTH, config.HUD_HEIGHT - 1), 1)

        title = self._font.render("TANKONS", True, (235, 235, 240))
        surface.blit(title, (22, (config.HUD_HEIGHT - title.get_height()) // 2))
        sub = self._small.render("tank battle", True, (110, 130, 160))
        surface.blit(sub, (22 + title.get_width() + 8, (config.HUD_HEIGHT - sub.get_height()) // 2 + 4))

        # scoreboard
        slot_w = 200
        total = slot_w * len(self._players)
        start_x = (config.WIDTH - total) // 2
        for i, p in enumerate(self._players):
            x = start_x + i * slot_w
            self._draw_player_slot(surface, p, x, match.score_of(p))

    def _draw_player_slot(self, surface: pg.Surface, p: Player, x: int, score: int) -> None:
        chip = pg.Rect(x, 10, 28, 28)
        pg.draw.rect(surface, p.colors["primary"], chip, border_radius=5)
        pg.draw.rect(surface, p.colors["accent"], chip, border_radius=5, width=2)

        name = self._font.render(p.name, True, p.colors["accent"])
        surface.blit(name, (x + 38, 6))

        score_surf = self._font.render(str(score), True, (235, 235, 240))
        surface.blit(score_surf, (x + 38, 26))

        alive = p.alive()
        dot_color = (130, 220, 120) if alive else (220, 80, 80)
        pg.draw.circle(surface, dot_color, (x + 150, 22), 5)
        status = self._small.render("ALIVE" if alive else "DOWN", True, dot_color)
        surface.blit(status, (x + 158, 16))
