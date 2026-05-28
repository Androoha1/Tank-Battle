"""Floor-sprite pickup entity."""
import math
import pygame as pg

from ..entities.entity import Entity
from .. import config


class PowerUpPickup(Entity):
    _font_cache: pg.font.Font | None = None
    _label_font_cache: pg.font.Font | None = None

    def __init__(self, x: float, y: float, effect_class) -> None:
        super().__init__(x, y)
        self._effect_class = effect_class
        self._radius = config.POWERUP_RADIUS
        self._spin = 0.0
        self._bob = 0.0

    @property
    def name(self) -> str:
        return self._effect_class.NAME

    @property
    def rect(self) -> pg.Rect:
        r = self._radius + 4
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._spin = (self._spin + dt * 0.18) % 360.0
        self._bob = (self._bob + dt * 0.005) % math.tau

    def apply(self, player, ctx) -> None:
        self._effect_class.dispatch(player, ctx)

    def draw(self, surface: pg.Surface) -> None:
        if PowerUpPickup._font_cache is None:
            PowerUpPickup._font_cache = pg.font.SysFont("arialblack", 18, bold=True)
        if PowerUpPickup._label_font_cache is None:
            PowerUpPickup._label_font_cache = pg.font.SysFont("arial", 12, bold=True)
        font = PowerUpPickup._font_cache
        label_font = PowerUpPickup._label_font_cache
        ec = self._effect_class

        cx = int(self._x)
        cy = int(self._y + math.sin(self._bob) * 3)

        # halo
        halo_r = self._radius * 3
        halo = pg.Surface((halo_r * 2, halo_r * 2), pg.SRCALPHA)
        pg.draw.circle(halo, (*ec.COLOR, 35), (halo_r, halo_r), halo_r)
        pg.draw.circle(halo, (*ec.COLOR, 80), (halo_r, halo_r), int(halo_r * 0.65))
        surface.blit(halo, (cx - halo_r, cy - halo_r))

        # body
        pg.draw.circle(surface, (250, 250, 250), (cx, cy), self._radius)
        pg.draw.circle(surface, ec.COLOR, (cx, cy), self._radius - 3)
        pg.draw.circle(surface, (255, 255, 255), (cx, cy), self._radius, 1)

        # icon
        icon = font.render(ec.ICON, True, (250, 250, 250))
        surface.blit(icon, icon.get_rect(center=(cx, cy)))

        # label
        label_y = cy + self._radius + 8
        shadow = label_font.render(ec.NAME, True, (0, 0, 0))
        text = label_font.render(ec.NAME, True, (255, 255, 255))
        surface.blit(shadow, shadow.get_rect(center=(cx + 1, label_y + 1)))
        surface.blit(text, text.get_rect(center=(cx, label_y)))
