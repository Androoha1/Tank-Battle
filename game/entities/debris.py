"""Rotating square chunk used during explosions."""
import math
import random
import pygame as pg

from .entity import Entity


class Debris(Entity):
    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        super().__init__(x, y)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2.0, 5.5)
        self._vx = math.cos(angle) * speed
        self._vy = math.sin(angle) * speed
        self._spin = random.uniform(-12, 12)
        self._angle = random.uniform(0, 360)
        self._size = random.randint(4, 8)
        self._color = color
        self._lifetime = random.randint(700, 1200)
        self._max = self._lifetime

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
        self._vx *= 0.97
        self._vy *= 0.97
        self._vy += 0.04  # slight gravity for top-down feel
        self._angle = (self._angle + self._spin) % 360

    def draw(self, surface: pg.Surface) -> None:
        t = self._lifetime / self._max
        if t <= 0:
            return
        size = self._size
        s = pg.Surface((size * 4, size * 4), pg.SRCALPHA)
        cx = s.get_width() // 2
        rect = pg.Rect(0, 0, size * 2, size * 2)
        rect.center = (cx, cx)
        alpha = int(255 * t)
        pg.draw.rect(s, (*self._color, alpha), rect, border_radius=2)
        pg.draw.rect(s, (10, 10, 14, alpha), rect, border_radius=2, width=1)
        rotated = pg.transform.rotate(s, self._angle)
        surface.blit(rotated, rotated.get_rect(center=(int(self._x), int(self._y))).topleft)
