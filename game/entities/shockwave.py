"""Expanding ring used as part of explosion visuals."""
import pygame as pg

from .entity import Entity


class Shockwave(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int] = (255, 255, 255),
        max_radius: float = 110.0,
        speed: float = 0.18,
        thickness: int = 3,
    ) -> None:
        super().__init__(x, y)
        self._radius = 4.0
        self._max = max_radius
        self._speed = speed
        self._color = color
        self._thickness = thickness

    @property
    def rect(self) -> pg.Rect:
        r = int(self._radius)
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._radius += self._speed * dt
        if self._radius >= self._max:
            self.kill()

    def draw(self, surface: pg.Surface) -> None:
        t = 1.0 - (self._radius / self._max)
        if t <= 0:
            return
        r = int(self._radius)
        alpha = int(220 * t * t)
        s = pg.Surface((r * 2 + 4, r * 2 + 4), pg.SRCALPHA)
        thickness = max(1, int(self._thickness * t))
        pg.draw.circle(s, (*self._color, alpha), (r + 2, r + 2), r, thickness)
        surface.blit(s, (int(self._x - r - 2), int(self._y - r - 2)))
