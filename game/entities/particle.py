"""Short-lived visual effect for explosions, etc."""
import math
import random
import pygame as pg

from .entity import Entity


class Particle(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        vx: float | None = None,
        vy: float | None = None,
        lifetime: int = 600,
        size: int = 4,
    ) -> None:
        super().__init__(x, y)
        if vx is None or vy is None:
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.8, 4.2)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
        self._vx = vx
        self._vy = vy
        self._color = color
        self._lifetime = lifetime
        self._max_lifetime = lifetime
        self._size = size

    @property
    def rect(self) -> pg.Rect:
        s = self._size
        return pg.Rect(int(self._x - s), int(self._y - s), s * 2, s * 2)

    def update(self, dt: float, ctx) -> None:
        self._lifetime -= dt
        if self._lifetime <= 0:
            self.kill()
            return
        self._x += self._vx
        self._y += self._vy
        self._vx *= 0.95
        self._vy *= 0.95

    def draw(self, surface: pg.Surface) -> None:
        t = self._lifetime / self._max_lifetime
        if t <= 0:
            return
        size = max(1, int(self._size * t))
        alpha = int(255 * t)
        s = pg.Surface((size * 2, size * 2), pg.SRCALPHA)
        pg.draw.circle(s, (*self._color, alpha), (size, size), size)
        surface.blit(s, (int(self._x - size), int(self._y - size)))
