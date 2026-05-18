"""Proximity mine dropped by a tank with the Mine power-up."""
import math
import random
import pygame as pg

from .entity import Entity
from .particle import Particle
from .debris import Debris
from .shockwave import Shockwave


class Mine(Entity):
    ARM_MS = 350
    LIFETIME_MS = 12000
    TRIGGER_RADIUS = 32
    KILL_RADIUS = 95
    COLOR = (200, 80, 80)

    def __init__(self, x: float, y: float, owner) -> None:
        super().__init__(x, y)
        self._owner = owner
        self._timer = self.LIFETIME_MS
        self._arm = self.ARM_MS
        self._pulse = 0.0
        self._exploded = False

    @property
    def rect(self) -> pg.Rect:
        r = 14
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    @property
    def owner(self):
        return self._owner

    def update(self, dt: float, ctx) -> None:
        self._timer -= dt
        self._arm = max(0, self._arm - dt)
        self._pulse = (self._pulse + dt * 0.012) % math.tau

        if self._timer <= 0:
            self._detonate(ctx)
            return

        if self._arm <= 0:
            for p in ctx.players:
                if not p.alive():
                    continue
                if p is self._owner:
                    continue
                dx = p.x - self._x
                dy = p.y - self._y
                if dx * dx + dy * dy <= self.TRIGGER_RADIUS * self.TRIGGER_RADIUS:
                    self._detonate(ctx)
                    return

    def _detonate(self, ctx) -> None:
        if self._exploded:
            return
        self._exploded = True
        self.kill()

        # Kill anyone in radius (including owner — proper mine etiquette).
        for p in ctx.players:
            if not p.alive():
                continue
            dx = p.x - self._x
            dy = p.y - self._y
            if dx * dx + dy * dy <= self.KILL_RADIUS * self.KILL_RADIUS:
                p.kill_player(ctx)

        # Visuals.
        ctx.add_shockwave(Shockwave(self._x, self._y, color=(255, 230, 130),
                                    max_radius=160, speed=0.34, thickness=4))
        ctx.add_shockwave(Shockwave(self._x, self._y, color=(255, 120, 60),
                                    max_radius=120, speed=0.26, thickness=3))
        for _ in range(45):
            ctx.add_particle(Particle(self._x, self._y, (255, 180, 80),
                                      lifetime=random.randint(400, 800),
                                      size=random.randint(3, 6)))
        for _ in range(10):
            ctx.add_debris(Debris(self._x, self._y, (90, 60, 50)))
        ctx.request_shake(intensity=12, duration_ms=380)
        ctx.request_flash((255, 200, 120), 70)

    def draw(self, surface: pg.Surface) -> None:
        cx, cy = int(self._x), int(self._y)
        # Glow that pulses faster as it nears detonation.
        pulse = (math.sin(self._pulse * 4 + self._timer * 0.001) + 1) / 2
        glow_r = 22
        glow = pg.Surface((glow_r * 2, glow_r * 2), pg.SRCALPHA)
        pg.draw.circle(glow, (255, 80, 80, int(40 + 90 * pulse)),
                       (glow_r, glow_r), glow_r)
        surface.blit(glow, (cx - glow_r, cy - glow_r))

        # Body.
        pg.draw.circle(surface, (40, 42, 50), (cx, cy), 12)
        pg.draw.circle(surface, (75, 78, 88), (cx, cy), 10)
        # Spikes (4).
        for ang in (0, 90, 180, 270):
            ax = cx + math.cos(math.radians(ang)) * 14
            ay = cy + math.sin(math.radians(ang)) * 14
            pg.draw.circle(surface, (50, 52, 60), (int(ax), int(ay)), 4)
        # Blinker.
        blink = (200, 60, 60) if pulse > 0.5 else (255, 200, 80)
        pg.draw.circle(surface, blink, (cx, cy), 4)
