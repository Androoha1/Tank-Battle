"""Bouncing projectile."""
import math
import pygame as pg

from .entity import Entity
from .. import config


class Shot(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        angle_deg: float,
        owner,
        color,
        *,
        radius: int | None = None,
        speed: float | None = None,
        max_bounces: int | None = None,
        lifetime_ms: int | None = None,
    ) -> None:
        super().__init__(x, y)
        self._angle = angle_deg
        sp = speed if speed is not None else config.SHOT_SPEED
        rad = math.radians(angle_deg)
        self._vx = math.cos(rad) * sp
        self._vy = -math.sin(rad) * sp
        self._radius = radius if radius is not None else config.SHOT_RADIUS
        self._bounces_left = max_bounces if max_bounces is not None else config.SHOT_MAX_BOUNCES
        self._lifetime = lifetime_ms if lifetime_ms is not None else config.SHOT_LIFETIME_MS
        self._grace = config.SHOT_OWNER_GRACE_MS
        self._owner = owner
        self._color = color
        self._trail: list[tuple[float, float]] = []

    @property
    def owner(self):
        return self._owner

    @property
    def can_hit_owner(self) -> bool:
        return self._grace <= 0

    @property
    def rect(self) -> pg.Rect:
        r = self._radius
        return pg.Rect(int(self._x - r), int(self._y - r), r * 2, r * 2)

    def update(self, dt: float, ctx) -> None:
        self._lifetime -= dt
        self._grace = max(0, self._grace - dt)
        if self._lifetime <= 0:
            self.kill()
            return

        self._trail.append((self._x, self._y))
        if len(self._trail) > 9:
            self._trail.pop(0)

        # Axis-separated movement -> clean reflections.
        self._x += self._vx
        if self._collide_walls_axis(ctx.walls, axis="x") and self._bounces_left < 0:
            self.kill()
            return
        self._bounce_screen()
        if self._bounces_left < 0:
            self.kill()
            return

        self._y += self._vy
        if self._collide_walls_axis(ctx.walls, axis="y") and self._bounces_left < 0:
            self.kill()
            return
        self._bounce_screen()
        if self._bounces_left < 0:
            self.kill()

    def _collide_walls_axis(self, walls, axis: str) -> bool:
        r = self._radius
        srect = self.rect
        for wall in walls:
            if srect.colliderect(wall.rect):
                if axis == "x":
                    if self._vx > 0:
                        self._x = wall.rect.left - r
                    else:
                        self._x = wall.rect.right + r
                    self._vx *= -1
                else:
                    if self._vy > 0:
                        self._y = wall.rect.top - r
                    else:
                        self._y = wall.rect.bottom + r
                    self._vy *= -1
                self._bounces_left -= 1
                return True
        return False

    def _bounce_screen(self) -> None:
        r = self._radius
        top = config.HUD_HEIGHT
        if self._x < r:
            self._x = r
            self._vx *= -1
            self._bounces_left -= 1
        elif self._x > config.WIDTH - r:
            self._x = config.WIDTH - r
            self._vx *= -1
            self._bounces_left -= 1
        if self._y < top + r:
            self._y = top + r
            self._vy *= -1
            self._bounces_left -= 1
        elif self._y > config.HEIGHT - r:
            self._y = config.HEIGHT - r
            self._vy *= -1
            self._bounces_left -= 1

    def draw(self, surface: pg.Surface) -> None:
        # Motion trail.
        n = len(self._trail)
        for i, (tx, ty) in enumerate(self._trail):
            t = (i + 1) / max(n, 1)
            radius = max(1, int(self._radius * t))
            alpha = int(120 * t)
            s = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
            pg.draw.circle(s, (*self._color, alpha), (radius, radius), radius)
            surface.blit(s, (tx - radius, ty - radius), special_flags=pg.BLEND_PREMULTIPLIED)

        # Outer glow.
        glow_r = self._radius * 3
        glow = pg.Surface((glow_r * 2, glow_r * 2), pg.SRCALPHA)
        pg.draw.circle(glow, (*self._color, 50), (glow_r, glow_r), glow_r)
        pg.draw.circle(glow, (*self._color, 110), (glow_r, glow_r), self._radius * 2)
        surface.blit(glow, (self._x - glow_r, self._y - glow_r))

        # Core.
        cx, cy = int(self._x), int(self._y)
        pg.draw.circle(surface, (255, 255, 255), (cx, cy), self._radius)
        pg.draw.circle(surface, self._color, (cx, cy), self._radius - 1)
