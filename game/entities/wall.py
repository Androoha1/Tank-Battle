"""Static collision geometry."""
import pygame as pg

from .entity import Entity
from .. import config


class Wall(Entity):
    def __init__(self, x: float, y: float, w: int, h: int) -> None:
        super().__init__(x, y)
        self._rect = pg.Rect(int(x), int(y), int(w), int(h))
        self._image = self._render(int(w), int(h))

    @property
    def rect(self) -> pg.Rect:
        return self._rect

    @staticmethod
    def _render(w: int, h: int) -> pg.Surface:
        s = pg.Surface((w, h), pg.SRCALPHA)
        pg.draw.rect(s, config.WALL_SHADOW, (0, 0, w, h), border_radius=5)
        pg.draw.rect(s, config.WALL_COLOR, (1, 1, w - 2, h - 3), border_radius=4)
        pg.draw.rect(s, config.WALL_HIGHLIGHT, (2, 2, w - 4, max(1, h // 3)), border_radius=3)
        pg.draw.rect(s, config.WALL_SHADOW, (0, 0, w, h), width=1, border_radius=5)
        return s

    def update(self, dt: float, ctx) -> None:
        pass

    def draw(self, surface: pg.Surface) -> None:
        surface.blit(self._image, self._rect.topleft)
