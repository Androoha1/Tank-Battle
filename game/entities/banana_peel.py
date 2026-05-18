"""A banana peel left behind by the Banana power-up.

Living on the floor, it triggers a 4-second Spinner debuff on the first
non-owner tank that drives over it, then disappears in a puff of yellow.
"""
import math
import pygame as pg

from .entity import Entity
from .particle import Particle
from ..powerups.spinner import Spinner


class BananaPeel(Entity):
    LIFETIME_MS = 8000
    RADIUS = 14

    def __init__(self, x: float, y: float, owner) -> None:
        super().__init__(x, y)
        self._owner = owner
        self._lifetime = self.LIFETIME_MS
        self._wobble = 0.0

    @property
    def rect(self) -> pg.Rect:
        r = self.RADIUS
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._lifetime -= dt
        if self._lifetime <= 0:
            self.kill()
            return
        self._wobble = (self._wobble + dt * 0.005) % math.tau

        for p in ctx.players:
            if not p.alive() or p is self._owner:
                continue
            if self.rect.colliderect(p.rect):
                spin = Spinner(0, 0)
                spin.activate()
                p.add_effect(spin)
                for _ in range(10):
                    ctx.add_particle(Particle(
                        self._x, self._y, (255, 220, 60),
                        lifetime=300, size=3,
                    ))
                ctx.audio.play_pickup()
                self.kill()
                return

    def draw(self, surface: pg.Surface) -> None:
        t = max(0.25, self._lifetime / self.LIFETIME_MS)
        alpha = int(255 * t)
        cx, cy = int(self._x), int(self._y + math.sin(self._wobble) * 1.5)

        body = pg.Surface((36, 28), pg.SRCALPHA)
        # main yellow peel
        pg.draw.ellipse(body, (255, 230, 80, alpha), (2, 6, 32, 16))
        # darker rim
        pg.draw.ellipse(body, (190, 140, 30, alpha), (2, 6, 32, 16), 2)
        # brown tips
        pg.draw.circle(body, (130, 90, 30, alpha), (4, 14), 3)
        pg.draw.circle(body, (130, 90, 30, alpha), (32, 14), 3)
        # highlight streak
        pg.draw.arc(body, (255, 250, 200, alpha), (4, 8, 28, 12), 0.3, 2.8, 1)
        surface.blit(body, body.get_rect(center=(cx, cy)))
